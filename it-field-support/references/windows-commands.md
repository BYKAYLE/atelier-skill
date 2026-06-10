# Windows 진단/해결 명령어 레퍼런스

## 1. 오피스 라이센스/설치

### 진단
```powershell
# 오피스 설치 경로 확인 (버전별)
$officePath = @(
  "C:\Program Files\Microsoft Office\Office16",
  "C:\Program Files (x86)\Microsoft Office\Office16",
  "C:\Program Files\Microsoft Office\Office15"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

# 라이센스 상태 확인
cscript "$officePath\ospp.vbs" /dstatus

# 전체 라이센스 정보
cscript "$officePath\ospp.vbs" /dstatusall

# 오피스 버전 확인
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration" -ErrorAction SilentlyContinue | Select-Object -Property VersionToReport, Platform

# Microsoft 365 설치 확인
Get-WmiObject -Query "SELECT * FROM Win32_Product WHERE Name LIKE '%Office%' OR Name LIKE '%365%'"
```

### 해결
```powershell
# Level 1: 강제 인증
cscript "$officePath\ospp.vbs" /act

# Level 2: 키 제거 후 재입력
# 현재 등록된 키의 마지막 5자리 확인 후
cscript "$officePath\ospp.vbs" /unpkey:마지막5자리
cscript "$officePath\ospp.vbs" /inpkey:XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
cscript "$officePath\ospp.vbs" /act

# Level 2-1: KMS 서버 지정 (회사 환경)
cscript "$officePath\ospp.vbs" /sethst:kms.company.local
cscript "$officePath\ospp.vbs" /setprt:1688
cscript "$officePath\ospp.vbs" /act

# Level 3: 토큰 초기화
Stop-Service osppsvc -Force
Remove-Item "C:\ProgramData\Microsoft\OfficeSoftwareProtectionPlatform\tokens.dat" -Force
Start-Service osppsvc
cscript "$officePath\ospp.vbs" /act

# Level 4: 오피스 완전 제거
# SaRA 사용 (Microsoft 공식)
# https://aka.ms/SaRA-officeUninstallFromPC 에서 다운로드 후:
SaRACmd.exe -S OfficeScrubScenario -AcceptEula

# 수동 제거
Get-WmiObject -Query "SELECT * FROM Win32_Product WHERE Name LIKE '%Office%'" | ForEach-Object { $_.Uninstall() }
Remove-Item "C:\Program Files\Microsoft Office" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Program Files (x86)\Microsoft Office" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "HKLM:\SOFTWARE\Microsoft\Office" -Recurse -ErrorAction SilentlyContinue
Remove-Item "HKCU:\SOFTWARE\Microsoft\Office" -Recurse -ErrorAction SilentlyContinue

# Level 4-1: ODT(Office Deployment Tool)로 클린 설치
# setup.exe /configure install.xml

# Level 5: 시스템 파일 복구 후 재설치
sfc /scannow
DISM /Online /Cleanup-Image /RestoreHealth
# 이후 Level 4 재시도
```

---

## 2. 네트워크 연결

### 진단
```powershell
# NIC 상태
Get-NetAdapter | Format-Table Name, Status, LinkSpeed, MediaConnectionState

# IP 설정 전체
ipconfig /all

# 게이트웨이 응답
$gw = (Get-NetRoute -DestinationPrefix "0.0.0.0/0" | Select-Object -First 1).NextHop
Test-Connection $gw -Count 2

# 외부 연결
Test-Connection 8.8.8.8 -Count 2

# DNS 해석
nslookup google.com
Resolve-DnsName google.com

# IP 충돌 확인
arp -a

# 라우팅 테이블
route print

# Wi-Fi 정보 (무선인 경우)
netsh wlan show interfaces
netsh wlan show profiles
```

### 해결
```powershell
# Level 1: IP 갱신
ipconfig /release
ipconfig /renew

# Level 2: DNS 캐시 플러시 + DNS 변경
ipconfig /flushdns
# DNS 변경 (어댑터명 확인 후)
netsh interface ip set dns "이더넷" static 8.8.8.8
netsh interface ip add dns "이더넷" 8.8.4.4 index=2

# Level 3: NIC 재시작
Disable-NetAdapter -Name "이더넷" -Confirm:$false
Start-Sleep -Seconds 3
Enable-NetAdapter -Name "이더넷"

# Level 4: Winsock/TCP 스택 초기화 (재부팅 필요)
netsh winsock reset
netsh int ip reset
# 재부팅 안내

# Level 5: 드라이버 재설치
# 장치 관리자에서 수동 진행 안내
pnputil /scan-devices
```

---

## 3. 공유폴더/NAS

### 진단
```powershell
# 대상 호스트 ping
Test-Connection NAS주소 -Count 2

# SMB 포트 확인
Test-NetConnection NAS주소 -Port 445

# SMB 클라이언트 설정
Get-SmbClientConfiguration | Select-Object EnableSMB1Protocol, EnableSMB2Protocol

# 현재 네트워크 드라이브
net use
Get-SmbConnection

# 공유 목록 보기
net view \\NAS주소

# 자격 증명 관리자
cmdkey /list

# 방화벽에서 SMB 차단 여부
Get-NetFirewallRule -DisplayName "*SMB*" | Format-Table DisplayName, Enabled, Action
```

### 해결
```powershell
# Level 1: 자격 증명 제거 후 재연결
cmdkey /delete:NAS주소
net use \\NAS주소\공유폴더 /user:사용자 비밀번호

# Level 2: SMB 프로토콜 버전 맞춤
# SMB1 활성화 (구형 NAS용, 보안 위험 고지 필수)
Set-SmbClientConfiguration -EnableSMB1Protocol $true -Force
# SMB1 비활성화 (보안 강화)
Set-SmbClientConfiguration -EnableSMB1Protocol $false -Force

# Level 3: 방화벽 허용
New-NetFirewallRule -DisplayName "Allow SMB" -Direction Inbound -Protocol TCP -LocalPort 445 -Action Allow

# Level 4: 네트워크 검색 활성화
Get-NetFirewallRule -DisplayGroup "Network Discovery" | Set-NetFirewallRule -Enabled True
Get-NetFirewallRule -DisplayGroup "File and Printer Sharing" | Set-NetFirewallRule -Enabled True

# Level 5: Guest 인증 허용 (보안 고지 필수)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" -Name "AllowInsecureGuestAuth" -Value 1 -Type DWord
```

---

## 4. 프린터

### 진단
```powershell
# 프린터 목록 및 상태
Get-Printer | Format-Table Name, PrinterStatus, PortName, DriverName

# 스풀러 서비스 상태
Get-Service Spooler

# 대기 중인 인쇄 작업
Get-PrintJob -PrinterName "프린터이름"

# 프린터 포트 확인
Get-PrinterPort | Format-Table Name, PrinterHostAddress

# 네트워크 프린터 연결 확인
Test-NetConnection 프린터IP -Port 9100
Test-NetConnection 프린터IP -Port 631
```

### 해결
```powershell
# Level 1: 인쇄 작업 제거 + 스풀러 재시작
Get-PrintJob -PrinterName "프린터이름" | Remove-PrintJob
Restart-Service Spooler

# Level 2: 프린터 삭제 후 재추가
Remove-Printer -Name "프린터이름"
Add-Printer -Name "프린터이름" -DriverName "드라이버명" -PortName "IP_포트"

# Level 3: 스풀러 완전 초기화
Stop-Service Spooler -Force
Remove-Item "C:\Windows\System32\spool\PRINTERS\*" -Force
Start-Service Spooler

# Level 4: 드라이버 재설치
Remove-PrinterDriver -Name "드라이버명"
# 드라이버 재설치는 제조사 설치 파일 또는 Windows Update 사용
pnputil /add-driver 드라이버경로\*.inf /install
```

---

## 5. 시스템 성능/서비스

### 진단
```powershell
# 시스템 기본 정보
systeminfo | Select-String "OS Name|Total Physical Memory|System Boot Time|OS Version"

# CPU 상위 프로세스
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet

# 메모리 상위 프로세스
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10 Name, @{N='Memory(MB)';E={[math]::Round($_.WorkingSet/1MB,1)}}

# 디스크 사용량
Get-Volume | Format-Table DriveLetter, FileSystemLabel, @{N='Size(GB)';E={[math]::Round($_.Size/1GB,1)}}, @{N='Free(GB)';E={[math]::Round($_.SizeRemaining/1GB,1)}}

# 중지된 주요 서비스
Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -eq 'Stopped' } | Format-Table Name, DisplayName

# 최근 시스템 에러 (이벤트 로그)
Get-EventLog -LogName System -EntryType Error -Newest 20 | Format-Table TimeGenerated, Source, Message -Wrap

# 시작 프로그램
Get-CimInstance Win32_StartupCommand | Format-Table Name, Command, Location

# 부팅 후 경과 시간
(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
```

### 해결
```powershell
# Level 1: 불필요한 프로세스 종료
Stop-Process -Name "프로세스명" -Force

# Level 2: 임시 파일 정리
Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue

# Level 3: 서비스 재시작
Restart-Service "서비스명"

# Level 4: 시스템 파일 복구
sfc /scannow
DISM /Online /Cleanup-Image /RestoreHealth

# Level 5: 디스크 오류 검사
chkdsk C: /f /r
# 재부팅 시 실행됨을 안내
```

---

## 6. AD/계정/권한

### 진단
```powershell
# 현재 사용자 정보
whoami /all

# 도메인 참여 상태
(Get-WmiObject Win32_ComputerSystem).PartOfDomain
(Get-WmiObject Win32_ComputerSystem).Domain

# 도메인 컨트롤러 연결
nltest /dsgetdc:도메인명

# 보안 채널 상태
Test-ComputerSecureChannel

# 적용된 그룹 정책
gpresult /r

# 계정 잠금 확인 (DC에서 실행)
# Search-ADAccount -LockedOut
```

### 해결
```powershell
# Level 1: 보안 채널 복구
Test-ComputerSecureChannel -Repair -Credential (Get-Credential)

# Level 2: 그룹 정책 강제 갱신
gpupdate /force

# Level 3: 도메인 재가입
# 먼저 도메인에서 분리
Remove-Computer -UnjoinDomainCredential (Get-Credential) -Force -Restart
# 재부팅 후 재가입
Add-Computer -DomainName "도메인명" -Credential (Get-Credential) -Restart

# Level 4: 로컬 관리자 계정 활성화 (우회용)
net user Administrator /active:yes
net user Administrator 임시비밀번호
```

---

## 7. 디스크/저장 공간

### 진단
```powershell
# 드라이브별 용량
Get-Volume | Format-Table DriveLetter, FileSystemLabel, @{N='Size(GB)';E={[math]::Round($_.Size/1GB,1)}}, @{N='Free(GB)';E={[math]::Round($_.SizeRemaining/1GB,1)}}

# 대용량 폴더 (C 드라이브 1단계)
Get-ChildItem C:\ -Directory -ErrorAction SilentlyContinue | ForEach-Object {
  [PSCustomObject]@{Name=$_.Name; SizeGB=[math]::Round((Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1GB,2)}
} | Sort-Object SizeGB -Descending | Select-Object -First 10

# 디스크 건강 상태
Get-PhysicalDisk | Format-Table FriendlyName, MediaType, HealthStatus, @{N='Size(GB)';E={[math]::Round($_.Size/1GB,1)}}

# 휴지통 용량
(New-Object -ComObject Shell.Application).NameSpace(0xa).Items() | Measure-Object Size -Sum

# Windows Update 캐시 용량
(Get-ChildItem "C:\Windows\SoftwareDistribution\Download" -Recurse -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum / 1GB
```

### 해결
```powershell
# Level 1: 디스크 정리
cleanmgr /d C: /VERYLOWDISK

# Level 2: Windows Update 캐시 삭제
Stop-Service wuauserv -Force
Remove-Item "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force
Start-Service wuauserv

# Level 3: WinSxS 컴포넌트 정리
DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase

# Level 4: 대용량 파일 목록 제공 (삭제는 사용자 결정)
Get-ChildItem C:\ -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Length -gt 500MB } |
  Sort-Object Length -Descending |
  Select-Object FullName, @{N='Size(GB)';E={[math]::Round($_.Length/1GB,2)}}

# Level 5: 디스크 오류 검사
chkdsk C: /f /r
```

---

## 공통: 상태 백업 명령어

조치 전 반드시 현재 상태를 백업한다:

```powershell
# 네트워크 설정 백업
netsh interface ip show config > "$env:USERPROFILE\Desktop\network-backup.txt"

# 레지스트리 키 백업
reg export "HKLM\SOFTWARE\Microsoft\Office" "$env:USERPROFILE\Desktop\office-reg-backup.reg"

# 방화벽 규칙 백업
netsh advfirewall export "$env:USERPROFILE\Desktop\firewall-backup.wfw"

# 프린터 설정 백업
Get-Printer | Export-Csv "$env:USERPROFILE\Desktop\printers-backup.csv"
```
