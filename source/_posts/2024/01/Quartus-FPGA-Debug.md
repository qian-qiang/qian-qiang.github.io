---
title: Quartus FPGA Debug
top: false
cover: false
toc: true
mathjax: true
date: 2024-01-06 09:35:48
password:
summary:
tags:
- FPGA
categories:
- FPGA
keywords:
description:
---
# Quartus FPGA Debug

## 系统调试工具比较

| 工具                            | 描述                                                                                                                                                                                                                              | 典型使用                                                                                                                                             |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| System Console                  | • 提供实时在系统内调试功能。• 允许您在没有处理器或其他软件的情况下读取和写入系统中的存储器映射(Memory Mapped)组件• 通过 Tcl 解释程序与设计中的硬件模块进行通信。• 允许您利用 Tcl 脚本语言的所有功能。• 支持 JTAG 和 TCP/IP 连接。 | 您需要执行系统级调试。例如，如果您有一个 Avalon® -MM slave 或者Avalon -ST 接口，那么您可以在传输级上调试设计。                                       |
| Transceiver Toolkit             | • 使您能够通过组合指标测试和调整收发器链路信号质量。• 物理介质附加层(PMA)的 Auto Sweeping 设置可帮助您找到最佳参数值。                                                                                                            | 您需要在完成设计之前调试或优化电路板布局的信号完整性。                                                                                               |
| Signal Tap Logic Analyzer       | • 使用 FPGA 资源• 对测试节点进行采样，并将信息输出到 Intel Quartus Prime 软件进行显示和分析。                                                                                                                                     | 您有备用的片上存储器，并且希望对硬件中运行的设计进行功能验证。                                                                                       |
| Signal Probe                    | 以递增方式将内部信号布线到 I/O 管脚，同时保留最后一次进行布局布线的设计结果。                                                                                                                                                     | 您有备用 I/O 管脚，并且想使用外部逻辑分析仪或示波器检查一小组控制管脚脚的操作。                                                                      |
| Logic Analyzer Interface (LAI)  | • 将较大一组信号多路复用到较少数量的备用 I/O 管脚。• 使您能够选择哪些信号通过 JTAG 连接切换到 I/O 管脚。                                                                                                                          | 您有需要使用外部逻辑分析仪进行验证的有限片上存储器和大量内部数据总线。逻辑分析仪供应商(例如Tektronics*和 Agilent*)提供与此工具的集成，以提高可用性。 |
| In-System Sources and Probes    | 提供使用 JTAG 接口将逻辑值驱动到内部节点和从内部节点采样逻辑值的简便方法。                                                                                                                                                        | 您想使用带虚拟按钮的前面板对 FPGA 进行原型设计。                                                                                                     |
| In-System Memory Content Editor | 显示并允许您编辑片上存储器。                                                                                                                                                                                                      | 您想对未连接到 Nios® II 处理器的片上存储器的内容进行查看和编辑。当您不想在系统中有 Nios II 调试内核时，您也可以使用此工具。                          |
| Virtual JTAG Interface          | 使您能够与 JTAG 接口进行通信，以便开发自定义应用程序。                                                                                                                                                                            | 您想要与设计中的自定义信号进行通信。                                                                                                                 |



## 对常用调试要求所建议的工具

| 要求                                | Signal Probe | 逻辑分析仪接口(LAI) | Signal Tap 逻辑分析仪 | 描述                                                                                                                                                                                                          |
| ----------------------------------- | ------------ | ------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| More Data Storage                   | N/A          | X                   | —                     | 包含 LAI 工具的外部逻辑分析仪使您能够存储比 Signal TapLogic Analyzer 更多的采集数据，因为外部逻辑分析仪能够提供对更大缓冲器的访问。Signal Probe 工具不采集数据，也不存储数据。                                |
| Faster Debugging                    | X            | X                   | —                     | 您可以将 LAI 或者 Signal Probe 工具同外部工具一起使用(例如：示波器和混合信号示波器(MSO))。此功能提供对时序模式的访问，允许您调试组合的数据流。                                                                |
| Minimal Effect on Logic Design      | X            | X (2)               | X (2)                 | Signal Probe 工具以递增方式将节点布线到管脚，而不影响设计逻辑。LAI 将最少的逻辑添加到设计中，从而需要更少的器件资源。Signal Tap Logic Analyzer 对设计的影响不大，因为 Compiler 将调试逻辑视为单独的设计分区。 |
| Short Compile and Recompile Time    | X            | X (2)               | X (2)                 | Signal Probe 使用递增布线将信号附加到之前保留的管脚上。此特性使您能够在更改源信号选择时快速地重新编译。Signal Tap Logic Analyzer 和 LAI 能够重新整修它们各自的设计分区以缩短重编译时间。                      |
| Sophisticated Triggering Capability | N/A          | N/A                 | X                     | Signal Tap Logic Analyzer 的触发功能可与商用逻辑分析仪相媲美。                                                                                                                                                |
| Low I/O Usage                       | —            | —                   | X                     | Signal Tap Logic Analyzer 不需要额外的输出管脚。LAI 和 Signal Probe 都需要 I/O 管脚约束(I/O pin assignments)。                                                                                                |
| Fast Data Acquisition               | N/A          | —                   | X                     | Signal Tap Logic Analyzer 能够在超过 200 MHz 的速度上采集数据。信号完整性问题限制了使用 LAI 的外部逻辑分析仪的采集速度。                                                                                      |
| No JTAG Connection Required         | X            | —                   | X                     | Signal Probe 和 Signal Tap 不需要主机进行调试。包含 LAI 的 FPGA 设计需要一个活动的 JTAG 连接到运行 Intel Quartus Prime 软件的主机。                                                                           |
| No External Equipment Required      | —            | —                   | X                     | Signal Tap Logic Analyzer 仅需要一个从运行 Intel QuartusPrime 软件或者独立的 Signal Tap Logic Analyzer 的主机的 JTAG连接。Signal Probe 和 LAI 需要使用外部调试设备，例如：万用表、示波器或逻辑分析仪。        |

注释：

1. • X 代表对相关功能所建议的工具。

   • —代表相关工具可用于此功能，但此工具可能无法提供最佳结果。

   • N/A 代表此功能不适用于所选工具。

2. 当使用增量编译时有效。

## 调试生态系统

| 调试工具                        | 从设计读取数据 | 在设计中输入值 | 备注                                                                 |
| ------------------------------- | -------------- | -------------- | -------------------------------------------------------------------- |
| Signal Tap Logic Analyzer,      | Yes            | No             | 针对探测寄存器传输级(RTL)网表中的信号进行优化的通用故障排除工具      |
| Logic Analyzer Interface        | ↑              | ↑              | ↑                                                                    |
| Signal Probe                    | ↑              | ↑              | ↑                                                                    |
| In-System Sources and Probes    | Yes            | Yes            | 这些工具能够：• 从您定义的断点读取数据• 在运行时期间将值输入到设计中 |
| Virtual JTAG Interface          | ↑              | ↑              | ↑                                                                    |
| System Console                  | ↑              | ↑              | ↑                                                                    |
| Transceiver Toolkit             | ↑              | ↑              | ↑                                                                    |
| In-System Memory Content Editor | ↑              | ↑              | ↑                                                                    |

> 来源 ： [system-debugging-tools-overview](https:/www.intel.cn/content/www/cn/zh/docs/programmable/683819/19-3/system-debugging-tools-overview.html)