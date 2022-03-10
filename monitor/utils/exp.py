#!usr/bin/python

import re

# with open('file.txt') as w:
#     file = w.read()


# txt = "The rain in Spain"
# # x = re.search("^The.*Spain$", txt)
# x = re.search(r"\d*\.\d*\.\d*", file)

# print(x.group())

# txt = "The rain in Spain"
# x = re.split("\s", txt)
# print(x)

# txt = "The rain in Spain"
# x = re.sub("S", "9", txt)
# print(x)

txt = '''
Type=forking
Restart=on-abort
NotifyAccess=none
RestartUSec=100ms
TimeoutStartUSec=1min 30s
TimeoutStopUSec=1min 30s
TimeoutAbortUSec=1min 30s
RuntimeMaxUSec=infinity
WatchdogUSec=0
WatchdogTimestampMonotonic=0
RootDirectoryStartOnly=no
RemainAfterExit=no
GuessMainPID=yes
MainPID=679
ControlPID=0
FileDescriptorStoreMax=0
NFileDescriptorStore=0
StatusErrno=0
Result=success
ReloadResult=success
CleanResult=success
UID=[not set]
GID=[not set]
NRestarts=0
OOMPolicy=stop
ExecMainStartTimestamp=Wed 2022-03-09 11:53:44 UTC
ExecMainStartTimestampMonotonic=4558781
ExecMainExitTimestampMonotonic=0
ExecMainPID=679
ExecMainCode=0
ExecMainStatus=0
ExecStart={ path=/usr/sbin/apachectl ; argv[]=/usr/sbin/apachectl start ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }
ExecStartEx={ path=/usr/sbin/apachectl ; argv[]=/usr/sbin/apachectl start ; flags= ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }
ExecReload={ path=/usr/sbin/apachectl ; argv[]=/usr/sbin/apachectl graceful ; ignore_errors=no ; start_time=[Thu 2022-03-10 00:00:09 UTC] ; stop_time=[Thu 2022-03-10 00:00:10 UTC] ; pid=21472 ; code=exited ; status=0 }
ExecReloadEx={ path=/usr/sbin/apachectl ; argv[]=/usr/sbin/apachectl graceful ; flags= ; start_time=[Thu 2022-03-10 00:00:09 UTC] ; stop_time=[Thu 2022-03-10 00:00:10 UTC] ; pid=21472 ; code=exited ; status=0 }
ExecStop={ path=/usr/sbin/apachectl ; argv[]=/usr/sbin/apachectl graceful-stop ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }
ExecStopEx={ path=/usr/sbin/apachectl ; argv[]=/usr/sbin/apachectl graceful-stop ; flags= ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }
Slice=system.slice
ControlGroup=/system.slice/apache2.service
MemoryCurrent=16412672
CPUUsageNSec=[not set]
EffectiveCPUs=
EffectiveMemoryNodes=
TasksCurrent=56
IPIngressBytes=[no data]
IPIngressPackets=[no data]
IPEgressBytes=[no data]
IPEgressPackets=[no data]
IOReadBytes=18446744073709551615
IOReadOperations=18446744073709551615
IOWriteBytes=18446744073709551615
IOWriteOperations=18446744073709551615
Delegate=no
CPUAccounting=no
CPUWeight=[not set]
StartupCPUWeight=[not set]
CPUShares=[not set]
StartupCPUShares=[not set]
CPUQuotaPerSecUSec=infinity
CPUQuotaPeriodUSec=infinity
AllowedCPUs=
AllowedMemoryNodes=
IOAccounting=no
IOWeight=[not set]
StartupIOWeight=[not set]
BlockIOAccounting=no
BlockIOWeight=[not set]
StartupBlockIOWeight=[not set]
MemoryAccounting=yes
DefaultMemoryLow=0
DefaultMemoryMin=0
MemoryMin=0
MemoryLow=0
MemoryHigh=infinity
MemoryMax=infinity
MemorySwapMax=infinity
MemoryLimit=infinity
DevicePolicy=auto
TasksAccounting=yes
TasksMax=2274
IPAccounting=no
Environment=APACHE_STARTED_BY_SYSTEMD=true
UMask=0022
LimitCPU=infinity
LimitCPUSoft=infinity
LimitFSIZE=infinity
LimitFSIZESoft=infinity
LimitDATA=infinity
LimitDATASoft=infinity
LimitSTACK=infinity
LimitSTACKSoft=8388608
LimitCORE=infinity
LimitCORESoft=0
LimitRSS=infinity
LimitRSSSoft=infinity
LimitNOFILE=524288
LimitNOFILESoft=1024
LimitAS=infinity
LimitASSoft=infinity
LimitNPROC=7580
LimitNPROCSoft=7580
LimitMEMLOCK=65536
LimitMEMLOCKSoft=65536
LimitLOCKS=infinity
LimitLOCKSSoft=infinity
LimitSIGPENDING=7580
LimitSIGPENDINGSoft=7580
LimitMSGQUEUE=819200
LimitMSGQUEUESoft=819200
LimitNICE=0
LimitNICESoft=0
LimitRTPRIO=0
LimitRTPRIOSoft=0
LimitRTTIME=infinity
LimitRTTIMESoft=infinity
OOMScoreAdjust=0
Nice=0
IOSchedulingClass=0
IOSchedulingPriority=0
CPUSchedulingPolicy=0
CPUSchedulingPriority=0
CPUAffinity=
CPUAffinityFromNUMA=no
NUMAPolicy=n/a
NUMAMask=
TimerSlackNSec=50000
CPUSchedulingResetOnFork=no
NonBlocking=no
StandardInput=null
StandardInputData=
StandardOutput=journal
StandardError=inherit
TTYReset=no
TTYVHangup=no
TTYVTDisallocate=no
SyslogPriority=30
SyslogLevelPrefix=yes
SyslogLevel=6
SyslogFacility=3
LogLevelMax=-1
LogRateLimitIntervalUSec=0
LogRateLimitBurst=0
SecureBits=0
CapabilityBoundingSet=cap_chown cap_dac_override cap_dac_read_search cap_fowner cap_fsetid cap_kill cap_setgid cap_setuid cap_setpcap cap_linux_immutable cap_net_bind_service cap_net_broadcast cap_net_admin cap_net_raw cap_ipc_lock cap_ipc_owner cap_sys_module cap_sys_rawio cap_sys_chroot cap_sys_ptrace cap_sys_pacct cap_sys_admin cap_sys_boot cap_sys_nice cap_sys_resource cap_sys_time cap_sys_tty_config cap_mknod cap_lease cap_audit_write cap_audit_control cap_setfcap cap_mac_override cap_mac_admin cap_syslog cap_wake_alarm cap_block_suspend cap_audit_read
AmbientCapabilities=
DynamicUser=no
RemoveIPC=no
MountFlags=
PrivateTmp=yes
PrivateDevices=no
ProtectKernelTunables=no
ProtectKernelModules=no
ProtectKernelLogs=no
ProtectControlGroups=no
PrivateNetwork=no
PrivateUsers=no
PrivateMounts=no
ProtectHome=no
ProtectSystem=no
SameProcessGroup=no
UtmpMode=init
IgnoreSIGPIPE=yes
NoNewPrivileges=no
SystemCallErrorNumber=0
LockPersonality=no
RuntimeDirectoryPreserve=no
RuntimeDirectoryMode=0755
StateDirectoryMode=0755
CacheDirectoryMode=0755
LogsDirectoryMode=0755
ConfigurationDirectoryMode=0755
TimeoutCleanUSec=infinity
MemoryDenyWriteExecute=no
RestrictRealtime=no
RestrictSUIDSGID=no
RestrictNamespaces=no
MountAPIVFS=no
KeyringMode=private
ProtectHostname=no
KillMode=mixed
KillSignal=15
RestartKillSignal=15
FinalKillSignal=9
SendSIGKILL=yes
SendSIGHUP=no
WatchdogSignal=6
Id=apache2.service
Names=apache2.service
Requires=system.slice -.mount sysinit.target
WantedBy=multi-user.target
Conflicts=shutdown.target
Before=apache-htcacheclean.service multi-user.target shutdown.target
After=systemd-journald.socket basic.target systemd-tmpfiles-setup.service -.mount network.target nss-lookup.target system.slice remote-fs.target sysinit.target
RequiresMountsFor=/tmp /var/tmp
Documentation=https://httpd.apache.org/docs/2.4/
Description=The Apache HTTP Server
LoadState=loaded
ActiveState=active
SubState=running
FragmentPath=/lib/systemd/system/apache2.service
UnitFileState=enabled
UnitFilePreset=enabled
StateChangeTimestamp=Thu 2022-03-10 00:00:10 UTC
StateChangeTimestampMonotonic=43589669780
InactiveExitTimestamp=Wed 2022-03-09 11:53:44 UTC
InactiveExitTimestampMonotonic=4180908
ActiveEnterTimestamp=Wed 2022-03-09 11:53:44 UTC
ActiveEnterTimestampMonotonic=4558792
ActiveExitTimestampMonotonic=0
InactiveEnterTimestampMonotonic=0
CanStart=yes
CanStop=yes
CanReload=yes
CanIsolate=no
StopWhenUnneeded=no
RefuseManualStart=no
RefuseManualStop=no
AllowIsolate=no
DefaultDependencies=yes
OnFailureJobMode=replace
IgnoreOnIsolate=no
NeedDaemonReload=no
JobTimeoutUSec=infinity
JobRunningTimeoutUSec=infinity
JobTimeoutAction=none
ConditionResult=yes
AssertResult=yes
ConditionTimestamp=Wed 2022-03-09 11:53:44 UTC
ConditionTimestampMonotonic=4180463
AssertTimestamp=Wed 2022-03-09 11:53:44 UTC
AssertTimestampMonotonic=4180463
Transient=no
Perpetual=no
StartLimitIntervalUSec=10s
StartLimitBurst=5
StartLimitAction=none
FailureAction=none
SuccessAction=none
InvocationID=3e78d3a1c2bf44358957fb541f076500
CollectMode=inactive
'''

x = re.search(r'ActiveState=\w*e\b', txt)

print(x.group())