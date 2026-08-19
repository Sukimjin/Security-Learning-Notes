# Windows 服务器基础配置笔记

> 适用场景：Windows Server 2016/2019/2022 运维、安全巡检
> 工具：PowerShell、命令提示符、远程桌面

---

## 一、账号与权限管理

### 1.1 本地账号操作（PowerShell）

```powershell
# 查看本地用户
Get-LocalUser

# 创建用户
New-LocalUser -Name "testuser" -Description "Test User" -NoPassword

# 设置密码
Set-LocalUser -Name "testuser" -Password (ConvertTo-SecureString "P@ssw0rd_2026" -AsPlainText -Force)

# 删除用户
Remove-LocalUser -Name "testuser"

# 启用 / 禁用账号
Disable-LocalUser -Name "testuser"
Enable-LocalUser -Name "testuser"

# 添加到组
Add-LocalGroupMember -Group "Remote Desktop Users" -Member "testuser"

# 查看组成员
Get-LocalGroupMember -Group "Administrators"

# 锁定密码策略
net accounts /lockoutthreshold:5 /lockoutduration:30 /lockoutwindow:30
```

### 1.2 域账号操作（需域环境）

```powershell
# 导入 AD 模块
Import-Module ActiveDirectory

# 查看用户
Get-ADUser -Filter *

# 查看组
Get-ADGroup -Filter *

# 添加用户到组
Add-ADGroupMember -Identity "Domain Admins" -Members "username"

# 查看组成员
Get-ADGroupMember -Identity "Domain Admins"

# 查找锁定账号
Search-ADAccount -LockedOut

# 查找长期未登录账号
Search-ADAccount -AccountInactive -TimeSpan 90.00:00:00
```

---

## 二、文件系统权限

### 2.1 icacls 命令

```cmd
# 查看文件 / 目录权限
icacls C:\Windows\System32\config

# 设置权限（赋予用户完全控制）
icacls "C:\folder" /grant "Username:(OI)(CI)F"

# 移除权限
icacls "C:\folder" /remove "Username"

# 拒绝权限
icacls "C:\folder" /deny "Everyone:(OI)(CI)F"

# 继承父目录权限
icacls "C:\folder" /inheritance:r
```

**常用权限标识**：
| 标识 | 含义 |
|---|---|
| `F` | 完全控制 |
| `M` | 修改 |
| `RX` | 读取和执行 |
| `R` | 读取 |
| `W` | 写入 |
| `(OI)` | 对象继承 |
| `(CI)` | 容器继承 |

### 2.2 PowerShell ACL

```powershell
# 获取 ACL
Get-Acl "C:\folder" | Format-List

# 设置 ACL
$acl = Get-Acl "C:\folder"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Username","FullControl","ContainerInherit,ObjectInherit","None","Allow")
$acl.AddAccessRule($rule)
Set-Acl "C:\folder" $acl
```

---

## 三、网络配置

### 3.1 基本网络命令

```cmd
# 查看网卡信息
ipconfig /all

# 查看路由表
route print

# 查看 DNS 缓存
ipconfig /displaydns

# 清除 DNS 缓存
ipconfig /flushdns

# 查看 ARP 表
arp -a

# 查看网络连接
netstat -ano

# 查找进程占用的端口
netstat -ano | findstr :80
tasklist /fi "PID eq 1234"

# 网络连通性测试
ping -t target.com
tracert target.com
pathping target.com

# 端口测试
Test-NetConnection -ComputerName target.com -Port 80
(New-Object System.Net.Sockets.TcpClient).ConnectAsync("target.com", 80)
```

### 3.2 DNS / DHCP 配置

```powershell
# 查看 DNS 设置
Get-DnsClientServerAddress -InterfaceAlias "Ethernet"

# 设置 DNS 服务器
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses ("8.8.8.8","8.8.4.4")

# 释放 / 续租 IP
ipconfig /release
ipconfig /renew
```

---

## 四、Windows 防火墙

### 4.1 基础命令

```powershell
# 查看防火墙状态
Get-NetFirewallProfile | Format-Table Name, Enabled

# 启用 / 禁用防火墙
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

# 查看规则
Get-NetFirewallRule | Format-Table DisplayName, Enabled, Direction, Action

# 创建入站规则
New-NetFirewallRule -DisplayName "Allow HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow

# 创建出站规则
New-NetFirewallRule -DisplayName "Block Telnet" -Direction Outbound -Protocol TCP -RemotePort 23 -Action Block

# 删除规则
Remove-NetFirewallRule -DisplayName "Allow HTTP"

# 启用规则
Enable-NetFirewallRule -DisplayName "Allow HTTP"

# 禁用规则
Disable-NetFirewallRule -DisplayName "Block Telnet"
```

### 4.2 高级配置（远程桌面允许特定 IP）

```powershell
# 创建规则：仅允许特定 IP 远程桌面
New-NetFirewallRule -DisplayName "RDP - Restricted" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 3389 `
    -RemoteAddress 192.168.1.0/24 `
    -Action Allow

# 默认拒绝规则
New-NetFirewallRule -DisplayName "RDP - Deny All" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 3389 `
    -Action Block
```

---

## 五、远程桌面服务

### 5.1 启用远程桌面

```powershell
# 启用远程桌面
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0

# 启用网络级别认证（NLA，更安全）
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name "UserAuthentication" -Value 1

# 防火墙放行
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"

# 查看连接会话
qwinsta

# 断开会话
logoff <SessionID>
rwinsta <SessionID>
```

### 5.2 修改默认端口（3389 → 其他）

```powershell
# 修改注册表
$port = 33389
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name "PortNumber" -Value $port

# 重启 TermService
Restart-Service TermService -Force

# 防火墙放行新端口
New-NetFirewallRule -DisplayName "RDP Custom Port" -Direction Inbound -Protocol TCP -LocalPort $port -Action Allow
Remove-NetFirewallRule -DisplayGroup "Remote Desktop"
```

---

## 六、Windows 服务管理

### 6.1 服务查看与配置

```powershell
# 查看所有服务
Get-Service | Format-Table Name, Status, StartType

# 查看特定服务
Get-Service -Name "WinRM"

# 启动 / 停止 / 重启
Start-Service -Name "WinRM"
Stop-Service -Name "WinRM"
Restart-Service -Name "WinRM"

# 设置启动类型
Set-Service -Name "WinRM" -StartupType Automatic
Set-Service -Name "RemoteRegistry" -StartupType Disabled

# 查看启动失败的服务
Get-Service | Where-Object {$_.Status -eq "Stopped" -and $_.StartType -eq "Automatic"}
```

### 6.2 计划任务

```powershell
# 查看所有计划任务
Get-ScheduledTask | Format-Table TaskName, State

# 查看特定任务
Get-ScheduledTask -TaskName "GoogleUpdateTaskMachineUA"

# 创建任务
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\scripts\backup.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At "2:00 AM"
Register-ScheduledTask -TaskName "Daily Backup" -Action $action -Trigger $trigger

# 删除任务
Unregister-ScheduledTask -TaskName "Suspicious Task" -Confirm:$false
```

---

## 七、日志与监控

### 7.1 事件查看器命令

```powershell
# 查看最近 100 条应用日志
Get-EventLog -LogName Application -Newest 100

# 查看最近 24 小时系统错误日志
Get-EventLog -LogName System -EntryType Error -After (Get-Date).AddHours(-24)

# 搜索特定 EventID
Get-EventLog -LogName Security -InstanceId 4625 -Newest 50

# 清空日志
Clear-EventLog -LogName Application

# 导出日志
Get-EventLog -LogName System -After "2026-08-01" | Export-Csv C:\logs\system.csv
```

### 7.2 关键 EventID 速查

| 类别 | EventID | 说明 |
|---|---|---|
| 登录成功 | 4624 | 账户登录成功 |
| 登录失败 | 4625 | 账户登录失败 |
| 账户锁定 | 4740 | 账户被锁定 |
| 特权使用 | 4672 | 特殊权限分配给新登录 |
| 进程创建 | 4688 | 新进程已创建 |
| 服务安装 | 7045 | 服务已安装 |
| 用户创建 | 4720 | 用户账户已创建 |
| 用户添加到组 | 4732 | 成员已添加到启用安全的全局组 |

### 7.3 性能监控

```powershell
# 实时 CPU 使用率
Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 2 -MaxSamples 5

# 内存使用
Get-Counter '\Memory\Available MBytes'

# 磁盘 IO
Get-Counter '\PhysicalDisk(_Total)\Disk Reads/sec','\PhysicalDisk(_Total)\Disk Writes/sec'

# 网络流量
Get-Counter '\Network Interface(*)\Bytes Total/sec'

# 监控特定时间窗口
Get-Counter -Counter "\Processor(_Total)\% Processor Time" -SampleInterval 2 -MaxSamples 30
```

---

## 八、Windows Defender

### 8.1 查看状态

```powershell
# 查看 Defender 状态
Get-MpComputerStatus | Format-List

# 查看威胁历史
Get-MpThreatDetection

# 查看已隔离文件
Get-MpThreat
```

### 8.2 扫描

```powershell
# 快速扫描
Start-MpScan -ScanType QuickScan

# 完全扫描
Start-MpScan -ScanType FullScan

# 自定义路径扫描
Start-MpScan -ScanType CustomScan -ScanPath "C:\Users"

# 更新病毒库
Update-MpSignature
```

### 8.3 排除项

```powershell
# 添加排除项
Add-MpPreference -ExclusionPath "C:\tools"
Add-MpPreference -ExclusionExtension ".log"

# 查看排除项
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath

# 移除排除项
Remove-MpPreference -ExclusionPath "C:\tools"
```

---

## 九、Windows Update

### 9.1 查看更新

```powershell
# 查看已安装更新
Get-HotFix | Format-Table HotFixID, Description, InstalledOn -AutoSize

# 查看未安装的更新
Get-WindowsUpdate

# 安装特定更新
Install-WindowsUpdate -KBArticleID "KB123456"

# 安装所有更新
Install-WindowsUpdate -AcceptAll -AutoReboot
```

### 9.2 设置更新策略

```powershell
# 查看更新设置
Get-WUSettings

# 禁用自动更新
Set-WUConfiguration -EnableAutoUpdate:$false
```

---

## 十、安全加固常用

### 10.1 关闭危险服务

```powershell
# 关闭 RemoteRegistry（远程注册表）
Stop-Service RemoteRegistry
Set-Service RemoteRegistry -StartupType Disabled

# 关闭 SMBv1
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force

# 关闭不必要的网络发现
Get-NetFirewallRule -DisplayGroup "Network Discovery" | Disable-NetFirewallRule
```

### 10.2 设置密码策略

```powershell
# 设置密码复杂度
secedit /export /cfg C:\sec.cfg
# 编辑 C:\sec.cfg 中的 MinimumPasswordLength、PasswordComplexity 等
secedit /configure /db C:\Windows\security\local.sdb /cfg C:\sec.cfg /areas SECURITYPOLICY

# 账户锁定策略
net accounts /lockoutthreshold:5 /lockoutduration:30 /lockoutwindow:30
```

### 10.3 审计策略

```powershell
# 启用登录审计
auditpol /set /category:"Logon/Logoff" /success:enable /failure:enable

# 启用进程跟踪
auditpol /set /category:"Detailed Tracking" /success:enable

# 启用对象访问审计
auditpol /set /category:"Object Access" /success:enable /failure:enable

# 查看当前策略
auditpol /get /category:*
```

### 10.4 关闭默认共享

```powershell
# 关闭 C$、D$ 等默认共享
net share C$ /delete
net share D$ /delete
net share ADMIN$ /delete

# 永久关闭：修改注册表
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters' -Name "AutoShareWks" -Value 0
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters' -Name "AutoShareServer" -Value 0

# 重启 server 服务
Restart-Service LanmanServer
```

### 10.5 启用 BitLocker

```powershell
# 查看 BitLocker 状态
Get-BitLockerVolume

# 启用 BitLocker（需要 TPM）
Enable-BitLocker -MountPoint "C:" -EncryptionMethod Aes256 -UsedSpaceOnly

# 备份恢复密钥
$key = (Get-BitLockerVolume -MountPoint "C:").KeyProtector.RecoveryPassword
Backup-BitLockerKeyProtector -MountPoint "C:" -KeyProtectorId $key
```

---

## 十一、远程管理（PowerShell Remoting）

### 11.1 启用 WinRM

```powershell
# 启用 WinRM
Enable-PSRemoting -Force

# 查看 WinRM 状态
Get-Service WinRM

# 配置监听
Set-WSManQuickConfig

# 允许特定 IP 远程管理
New-NetFirewallRule -DisplayName "WinRM - Restricted" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 5985,5986 `
    -RemoteAddress 192.168.1.0/24 `
    -Action Allow
```

### 11.2 连接远程服务器

```powershell
# 单台服务器
Enter-PSSession -ComputerName server01 -Credential domain\username

# 执行远程命令
Invoke-Command -ComputerName server01 -ScriptBlock {Get-Service} -Credential domain\username

# 批量执行
$computers = "server01","server02","server03"
Invoke-Command -ComputerName $computers -ScriptBlock {Get-HotFix | Select-Object HotFixID, InstalledOn} -Credential domain\username
```

---

## 十二、常用配置路径

| 服务 | 路径 |
|---|---|
| 系统日志 | `C:\Windows\System32\winevt\Logs\` |
| 应用日志 | `事件查看器 → Windows Logs → Application` |
| IIS 配置 | `%windir%\system32\inetsrv\config\` |
| 注册表 | `regedit` |
| 组策略 | `gpedit.msc`（专业版）/ `secpol.msc` |
| 本地安全策略 | `secpol.msc` |
| 计算机管理 | `compmgmt.msc` |
| 服务管理 | `services.msc` |
| 设备管理器 | `devmgmt.msc` |
| 任务计划 | `taskschd.msc` |

---

## 十三、参考

- Microsoft Docs：<https://docs.microsoft.com/zh-cn/>
- PowerShell 官方文档
- Windows Server 官方文档
- 各服务（IIS、SQL Server、Active Directory）官方文档