# 010 Editor PNG.bt — 重写版

010 Editor 的 PNG / APNG 二进制模板(Binary Template),按 PNG 1.2 / PNG-3(ISO 17442)/ APNG 规范完整重写。
除正常解析外,专门面向 **CTF Misc 图片取证** 做了强化:凡是 PNG 里不该出现的东西都会用醒目的**品红色**标出,并把其中隐藏的文本提取打印到 Output 面板。

> 基于原版模板(Kevin O. Grover / RCS / Mister Wu)重写,原版存在的问题见下文。

## 安装

1. 把 `PNG.bt` 放到任意目录(推荐 `文档\SweetScape\010 Templates\`);
2. 010 Editor 菜单 `Templates` → `View Installed Templates...` → `Add`,选中 `PNG.bt`;
3. 打开任意 `.png` / `.apng` 文件即可自动运行(或 `Templates` 菜单手动运行)。

> 如果之前安装了仓库(Repository)自带的旧版 PNG.bt,建议删除或禁用,避免打开文件时自动运行旧模板。
> 旧模板遇到 IEND 后有数据、文件被截断等情况会直接报错退出(实测 `Template passed end of file at variable 'data'`)。

## 相对旧版修复的问题

| 问题 | 旧版行为 | 本版 |
| --- | --- | --- |
| 解析报错 | `tEXt` / `fdAT` 解析器引用了未定义的 `length` 变量;`zTXt` / `iTXt` 被写成 `zEXt` / `iEXt`,永远匹配不上 | 每个解析器显式传入长度,块名全部修正 |
| 越界读取 | 变长字符串可能一路读到 CRC 甚至文件末尾(截断文件直接崩溃) | 所有读数按块长钳制,坏块自动重新同步,不再崩溃 |
| 高亮颜色 | 隔行铺 `cLtGray` 底色,块类型无法区分 | 按块类型着色(见下),CRC 错误红色,异常数据品红 |
| 功能缺失 | 无 `iCCP` 分支;缺 `gAMA` / `tRNS` / `hIST` / `eXIf` / HDR 块等;无任何校验 | 覆盖 27 种块类型 + 结构校验 + CRC 校验 + 隐写检测 |

## 颜色图例(十六进制区背景色)

模板会通过 `ThemeIsDark()` 自动适配夜间/日间主题,两套配色分别针对两种主题原生设计(夜间主题下关闭了 010 的自动颜色缩放,避免整体变灰):

| 暗色主题 | 亮色主题 | 含义 |
| --- | --- | --- |
| 棕灰 | 淡紫 | PNG 文件签名 |
| 深绿 | 浅绿 | `IHDR` 图像头 |
| 深蓝 | 浅蓝 | `PLTE` 调色板 |
| 深橙 | 浅橙 | `IDAT` 图像数据 |
| 紫色 | 浅紫 | APNG 动画块 `acTL` / `fcTL` / `fdAT` |
| 青色 | 淡青 | 文本块 `tEXt` / `zTXt` / `iTXt`(藏文本高发区,一眼定位) |
| 石板灰 | 浅灰 | 其余辅助块(元数据) |
| 琥珀 | 亮黄 | 未知的**关键块**(按规范意味着文件无效) |
| 红 | 红 | CRC32 校验失败的块的 CRC 字段 |
| **品红** | **品红** | **不属于 PNG 的数据(藏数据!)** |

整块统一着色(含块头与数据);CRC 错误只把该块的 CRC 字段覆盖为红色。

## CTF 隐写检测

以下情况会以品红高亮,并在 Output 面板输出详情(大小、偏移、十六进制头部、可识别的文件格式、提取出的 ASCII 字符串):

- **签名前有数据**(文件头被塞了别的文件/文本);
- **IEND 之后有数据**(最经典的藏 flag 位置——追加 ZIP、文本等,会自动识别 ZIP/RAR/gzip/JPEG/PDF 等格式并提示);
- **IEND 之后伪装成块的数据**;
- 文件尾的残缺块 / 尾部垃圾。

同时,以下位置的内容会直接打印到 Output 面板:

- `tEXt` / `iTXt` 的明文内容(`关键字 = 内容`);
- `zTXt` / `iTXt`(压缩)/ `iCCP` / `eXIf` / 未知块数据中的 **ASCII 字符串扫描**——压缩数据后面追加的明文(常见套路)也能抓到;
- `tIME`(修改时间)、`pHYs`(DPI)、`gAMA`、`fcTL`(帧延时)等均以可读形式显示。

每个块输出一行摘要:`[序号] 偏移  块名  len=长度  CRC:ok/BAD`,文件末尾输出汇总(尺寸、颜色类型、块数、CRC 错误数、APNG 帧数与总时长、异常区域数)。

## 结构校验

- IHDR 必须是第一块、IEND 必须是最后一块,且 IEND 为空;
- 位深度 × 颜色类型组合合法性(规范表);
- 定长块(gAMA=4、cHRM=32、pHYs=9、tIME=7、fcTL=26、mDCv=24 ...)长度不符即报错并按原始数据展示;
- `PLTE` 长度必须是 3 的倍数且不出现在 IDAT 之后;`tRNS` / `hIST` / `bKGD` 与 PLTE / IDAT 的顺序;`tRNS` 条目数 ≤ 调色板数;
- IDAT 必须连续(APNG 的 fcTL/fdAT 除外);
- APNG `fcTL` / `fdAT` 序列号连续性、`acTL` 必须在 IDAT 前;
- 每个块的 CRC32 校验,失败红色高亮并列出存储值与计算值;
- 未知**关键块**报错(规范规定关键块未知即文件无效)。

## 本地测试

`make_tests.py` 生成 8 个边界测试文件,IHDR/全部辅助块/APNG/IEND 追加数据/签名前数据/坏 CRC/截断文件/尾部垃圾各一;
`run_all.bat`(配合 `test_png.1sc`)用 010 Editor 的 `-noui` 无界面模式逐个运行模板并把报告存到 `testfiles/report_*.txt`。

```bat
python make_tests.py
run_all.bat
```

当前版本 8/8 测试通过:无解析错误,异常位置与隐藏文本全部正确输出(见 `testfiles/report_*.txt`)。

## 许可

本项目以 [MIT License](LICENSE) 发布。

已确认 010 Editor / SweetScape 对模板没有任何专有许可要求(仓库提交条款只要求标准头部元数据,不含版权或许可限制),可自由使用、修改、再分发。

本模板为完全重写,不构成对旧版的衍生;仅在致谢中提及原版作者(Kevin O. Grover、RCS、Mister Wu),见 `PNG.bt` 文件头。
