# macOS 진단/해결 명령어 레퍼런스

## 1. 네트워크 연결

### 진단
```bash
# NIC 상태
ifconfig -a
networksetup -listallhardwareports

# IP 설정
ipconfig getifaddr en0          # 유선
ipconfig getifaddr en1          # Wi-Fi
networksetup -getinfo "Wi-Fi"
networksetup -getinfo "Ethernet"

# 게이트웨이 응답
netstat -rn | grep default
ping -c 3 $(netstat -rn | grep default | awk '{print $2}' | head -1)

# 외부 연결
ping -c 3 8.8.8.8

# DNS 해석
nslookup google.com
dig google.com
scutil --dns | head -30

# ARP 테이블 (IP 충돌 확인)
arp -a

# Wi-Fi 정보
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I
```

### 해결
```bash
# Level 1: IP 갱신
sudo ipconfig set en0 DHCP
sudo ipconfig set en1 DHCP

# Level 2: DNS 캐시 플러시 + DNS 변경
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
networksetup -setdnsservers "Wi-Fi" 8.8.8.8 8.8.4.4

# Level 3: NIC 재시작
sudo ifconfig en0 down
sudo ifconfig en0 up

# Level 4: 네트워크 설정 초기화
sudo rm -f /Library/Preferences/SystemConfiguration/NetworkInterfaces.plist
sudo rm -f /Library/Preferences/SystemConfiguration/preferences.plist
# 재부팅 안내
```

---

## 2. 공유폴더/NAS (SMB)

### 진단
```bash
# 대상 호스트 ping
ping -c 3 NAS주소

# SMB 포트 확인
nc -zv NAS주소 445

# SMB 연결 상태
smbutil statshares -a

# 공유 목록
smbutil lookup NAS주소

# 현재 마운트된 네트워크 드라이브
mount | grep smbfs
df -h | grep /Volumes

# NFS 확인
showmount -e NAS주소
```

### 해결
```bash
# Level 1: 기존 연결 해제 후 재연결
umount /Volumes/공유폴더
mount -t smbfs //사용자:비밀번호@NAS주소/공유폴더 /Volumes/공유폴더

# Level 2: Finder에서 연결
open "smb://NAS주소/공유폴더"

# Level 3: 키체인에서 자격 증명 삭제 후 재연결
security delete-internet-password -s NAS주소
# 이후 Finder에서 재연결 시 비밀번호 재입력

# Level 4: SMB 서명 설정 (호환성 문제 시)
# /etc/nsmb.conf 수정
echo "[default]" | sudo tee /etc/nsmb.conf
echo "signing_required=no" | sudo tee -a /etc/nsmb.conf
```

---

## 3. 프린터

### 진단
```bash
# 프린터 목록
lpstat -a
lpstat -p -d

# 인쇄 큐 확인
lpq -a

# CUPS 서비스 상태
cupsctl | grep -i status

# 네트워크 프린터 연결 확인
nc -zv 프린터IP 9100
nc -zv 프린터IP 631
```

### 해결
```bash
# Level 1: 인쇄 큐 비우기
cancel -a

# Level 2: CUPS 재시작
sudo launchctl stop org.cups.cupsd
sudo launchctl start org.cups.cupsd

# Level 3: 프린터 삭제 후 재추가
lpadmin -x 프린터이름
# 시스템 설정 > 프린터에서 재추가 안내

# Level 4: CUPS 초기화
sudo rm -rf /etc/cups/ppd/*
sudo rm -rf /etc/cups/printers.conf
sudo launchctl stop org.cups.cupsd
sudo launchctl start org.cups.cupsd
```

---

## 4. 시스템 성능

### 진단
```bash
# 시스템 정보
sw_vers
system_profiler SPHardwareDataType | grep -E "Model|Memory|Chip"
uptime

# CPU 상위 프로세스
ps aux --sort=-%cpu | head -11

# 메모리 상위 프로세스
ps aux --sort=-%mem | head -11

# 디스크 사용량
df -h

# 열려있는 파일/프로세스 수
lsof | wc -l

# 최근 시스템 로그
log show --last 30m --predicate 'eventType == logEvent AND logType == error' --style compact | tail -20
```

### 해결
```bash
# Level 1: 불필요한 프로세스 종료
kill -9 PID

# Level 2: 캐시 정리
sudo rm -rf ~/Library/Caches/*
sudo rm -rf /Library/Caches/*

# Level 3: DNS 캐시 + 메모리 해제
sudo dscacheutil -flushcache
sudo purge

# Level 4: 디스크 검사
diskutil verifyVolume /

# Level 5: 디스크 복구
diskutil repairVolume /
```

---

## 5. 디스크/저장 공간

### 진단
```bash
# 드라이브별 용량
df -h

# 대용량 폴더 (1단계)
sudo du -sh /* 2>/dev/null | sort -rh | head -10

# 사용자 폴더 용량
du -sh ~/Desktop ~/Documents ~/Downloads ~/Library 2>/dev/null

# 디스크 건강 상태
diskutil info / | grep -E "SMART|Type|Total"

# Time Machine 스냅샷 용량
tmutil listlocalsnapshots /
```

### 해결
```bash
# Level 1: 캐시/로그 정리
sudo rm -rf ~/Library/Caches/*
sudo rm -rf /private/var/log/asl/*.asl
sudo rm -rf ~/Library/Logs/*

# Level 2: Xcode 파생 데이터 (개발자용)
rm -rf ~/Library/Developer/Xcode/DerivedData/*
rm -rf ~/Library/Developer/Xcode/Archives/*

# Level 3: Time Machine 로컬 스냅샷 삭제
tmutil deletelocalsnapshots $(date +%Y-%m-%d)

# Level 4: 대용량 파일 목록 (삭제는 사용자 결정)
find / -type f -size +500M 2>/dev/null | head -20
```

---

## 공통: 상태 백업 명령어

```bash
# 네트워크 설정 백업
networksetup -getinfo "Wi-Fi" > ~/Desktop/network-backup.txt
networksetup -getinfo "Ethernet" >> ~/Desktop/network-backup.txt

# DNS 설정 백업
scutil --dns > ~/Desktop/dns-backup.txt

# 마운트 정보 백업
mount > ~/Desktop/mount-backup.txt
```
