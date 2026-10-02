# Explicit, reversible deployment provisioning; never invoked by application startup.
# ACC-2026-10-02-02. Run elevated. No keys, audit directory or networking changes.
[CmdletBinding()]
param(
    [ValidateSet('Apply', 'Verify', 'Rollback')][string]$Mode = 'Verify',
    [Parameter(Mandatory = $true)][string]$SnapshotPath
)
$ErrorActionPreference = 'Stop'
$target = 'C:\var\assurance\evidence-store'
$target = (Get-Item -LiteralPath $target).FullName.TrimEnd('\')
if ($target -cne 'C:\var\assurance\evidence-store') { throw 'Unexpected ACL target' }
$items = @((Get-Item -LiteralPath $target)) + @(Get-ChildItem -LiteralPath $target -Recurse -Force)
foreach ($item in $items) {
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point in ACL scope' }
    if ($item.FullName -ne $target -and -not $item.FullName.StartsWith($target + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'ACL scope escaped'
    }
}
$systemSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-18')
$adminSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-32-544')
$snapshotFull = [IO.Path]::GetFullPath($SnapshotPath)
if ($snapshotFull.StartsWith($target + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Snapshot must be outside target' }

function Set-OwnerSid([string]$Path, [string]$Sid) {
    & "$env:SystemRoot\System32\icacls.exe" $Path /setowner ("*" + $Sid) /Q
    if ($LASTEXITCODE -ne 0) { throw "Owner update failed: $Path" }
}
function Assert-Compliant {
    foreach ($item in $items) {
        $acl = Get-Acl -LiteralPath $item.FullName
        $ownerSid = $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
        # Newly created SQLite sidecars have the elevated supervisor's default
        # Administrators owner. That group is deny-only in workers; never allow
        # the shared user SID as owner (implicit WRITE_DAC would be unsafe).
        $owners = @($systemSid.Value, $adminSid.Value)
        if ($item.FullName -eq $target -or $item.Name -eq 'evidence.db') { $owners = @($systemSid.Value) }
        if ($ownerSid -notin $owners) { throw "Unsafe owner: $($item.FullName)" }
        $rules = @($acl.GetAccessRules($true, $true, [Security.Principal.SecurityIdentifier]))
        if ($rules.Count -ne 2) { throw "Unexpected rule count: $($item.FullName)" }
        foreach ($sid in @($adminSid, $systemSid)) {
            $match = @($rules | Where-Object { $_.IdentityReference.Value -eq $sid.Value })
            if ($match.Count -ne 1 -or $match[0].AccessControlType -ne 'Allow' -or
                $match[0].FileSystemRights -ne [Security.AccessControl.FileSystemRights]::FullControl) {
                throw "Unexpected DACL grant: $($item.FullName)"
            }
            if ($item.PSIsContainer -and $match[0].InheritanceFlags -ne
                ([Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [Security.AccessControl.InheritanceFlags]::ObjectInherit)) {
                throw 'Missing SQLite/future-file inheritance'
            }
        }
        [pscustomobject]@{ Path=$item.FullName; Sddl=$acl.Sddl }
    }
}
if ($Mode -eq 'Verify') { Assert-Compliant | ConvertTo-Json -Depth 4; exit 0 }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Elevated deployment shell required'
}
if ($Mode -eq 'Apply') {
    if (Test-Path -LiteralPath $snapshotFull) {
        # Idempotent rerun never overwrites original rollback evidence.
        $previousSnapshot = Get-Content -LiteralPath $snapshotFull -Raw | ConvertFrom-Json
        if ($previousSnapshot.Target -ne $target) { throw 'Existing snapshot target mismatch' }
        try { Assert-Compliant | ConvertTo-Json -Depth 4; exit 0 } catch {
            Write-Output 'Resuming scoped provisioning with original rollback snapshot preserved'
        }
    } else {
        $saved = @($items | ForEach-Object {
            $acl = Get-Acl -LiteralPath $_.FullName
            [pscustomobject]@{ Path=$_.FullName; Sddl=$acl.Sddl;
                OwnerSid=$acl.GetOwner([Security.Principal.SecurityIdentifier]).Value }
        })
        if (-not (Test-Path -LiteralPath (Split-Path -Parent $snapshotFull))) { throw 'Snapshot parent must already exist' }
        [pscustomobject]@{ Target=$target; Entries=$saved; CapturedUtc=[DateTime]::UtcNow.ToString('o') } |
            ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $snapshotFull -Encoding UTF8 -NoNewline
    }
    foreach ($item in $items) {
        Set-OwnerSid $item.FullName $systemSid.Value
        $acl = Get-Acl -LiteralPath $item.FullName
        $acl.SetAccessRuleProtection($true, $false)
        foreach ($rule in @($acl.GetAccessRules($true, $false, [Security.Principal.SecurityIdentifier]))) {
            [void]$acl.RemoveAccessRuleSpecific($rule)
        }
        $inherit = [Security.AccessControl.InheritanceFlags]::None
        if ($item.PSIsContainer) { $inherit = [Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [Security.AccessControl.InheritanceFlags]::ObjectInherit }
        foreach ($sid in @($systemSid, $adminSid)) {
            $rule = [Security.AccessControl.FileSystemAccessRule]::new($sid,
                [Security.AccessControl.FileSystemRights]::FullControl, $inherit,
                [Security.AccessControl.PropagationFlags]::None, [Security.AccessControl.AccessControlType]::Allow)
            [void]$acl.AddAccessRule($rule)
        }
        Set-Acl -LiteralPath $item.FullName -AclObject $acl
    }
    Assert-Compliant
    Write-Output "Rollback: powershell.exe -NoProfile -File scripts\windows\provision_sec008_evidence_acl.ps1 -Mode Rollback -SnapshotPath `"$snapshotFull`""
} else {
    $snapshot = Get-Content -LiteralPath $snapshotFull -Raw | ConvertFrom-Json
    if ($snapshot.Target -ne $target) { throw 'Rollback target mismatch' }
    foreach ($entry in $snapshot.Entries) {
        if ($entry.Path -ne $target -and -not $entry.Path.StartsWith($target + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Rollback entry outside scope' }
    }
    foreach ($entry in $snapshot.Entries) {
        if (-not (Test-Path -LiteralPath $entry.Path)) { throw "Rollback path missing: $($entry.Path)" }
        $acl = Get-Acl -LiteralPath $entry.Path
        $acl.SetSecurityDescriptorSddlForm($entry.Sddl, [Security.AccessControl.AccessControlSections]::Access)
        Set-Acl -LiteralPath $entry.Path -AclObject $acl
        Set-OwnerSid $entry.Path $entry.OwnerSid
    }
    # Files created after provisioning inherit the restored directory DACL.
    $known = @($snapshot.Entries | ForEach-Object { $_.Path })
    foreach ($item in $items | Where-Object { $_.FullName -notin $known }) {
        $acl = Get-Acl -LiteralPath $item.FullName
        foreach ($rule in @($acl.GetAccessRules($true, $false, [Security.Principal.SecurityIdentifier]))) { [void]$acl.RemoveAccessRuleSpecific($rule) }
        $acl.SetAccessRuleProtection($false, $false)
        Set-Acl -LiteralPath $item.FullName -AclObject $acl
        Set-OwnerSid $item.FullName $snapshot.Entries[0].OwnerSid
    }
    foreach ($entry in $snapshot.Entries) {
        $restored = Get-Acl -LiteralPath $entry.Path
        if ($restored.Sddl -ne $entry.Sddl) { throw "Rollback verification mismatch: $($entry.Path)" }
    }
    Write-Output 'ROLLBACK VERIFIED'
}
