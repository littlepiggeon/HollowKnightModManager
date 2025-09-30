# HollowKnightModManager CLI

# Usage

~ help 帮助

~ install <name> 安装模组  
~ uninstall <name> 删除模组  
~ disable <name> 禁用模组  
~ able <name> 启用模组  
~ list 列出模组  
~ update 更新版本索引  
~ upgrade <name> 升级模组

~ installapi 安装、升级Modding API

# Notice

hk-modding的模组列表出了毛病，导致xml解析器无法正常工作。  
不知道为什么PR被驳回了  
详情请见<https://github.com/hk-modding/modlinks/pull/2032>

<del>解决方案：

1. <del>打开`%APPDATA%\HollowKnightModManager\modlinks.xml`
2. <del>删除第二行的`xmlns="https://github.com/HollowKnight-Modding/HollowKnight.ModLinks/HollowKnight.ModManager"`
3. <del>由于HKMM会每天自动覆盖这个文件，所以每天运行前都要重复上述步骤

**现在HKMM会自动把这一行无法读取的除掉**  
