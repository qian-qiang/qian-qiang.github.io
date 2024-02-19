---
title: Memory Blocks in Cyclone IV Devices
top: false
cover: false
toc: true
mathjax: true
date: 2024-02-19 14:32:07
password:
summary:
tags:
- FPGA
categories:
- FPGA
keywords:
description:
---

原文地址 [Memory Blocks in Cyclone IV Devices](https://d2pgu9s4sfmw1s.cloudfront.net/UAM/Prod/Done/a062E00001d7f8hQAA/b2a0e94b-4425-b386-290e-92af04ecd145?response-content-disposition=inline%3Bfilename*%3DUTF-8%27%27cyiv-51003.pdf&Expires=2023672278&Key-Pair-Id=APKAJKRNIMMSNYXST6UA&Signature=dXoLW48nj4ZWqosK~mLTnuhnIczQNT2Cfb3YoUmcw5-HlQEbcyxOjOuLKmdS05MH11GGVCL2K3HxeoYaL3Ngh3hxYlQ6LJUMhh~MVqV4uRFijnotB0pvH1Sm8pZMPHNGAaM-4~7FDMiolcaT2zNsoA~MFl80D5al7KcJv4rU25~~S2vi4XpwEnv8d9RJWs8uhUle7l8ehHo1SIeSWC5BR19nCsobRdSCjxsMKBG7vjOHaX8~4Ejn39Lw97ZpLhpMkH6b6luzRXnnkqtg7qRufL-7H7~gIA8wXKEYaeeUIr-6ujRMzeMET7QZH34psPkBN94UNpVceIk38vvA2SUujQ__)

# Overview 
M9K blocks support the following features:
■ 8,192 memory bits per block （9,216 bits per block including parity）
■ Independent read-enable (rden) and write-enable (wren) signals for each port
■ Packed mode in which the M9K memory block is split into two 4.5 K single-port
RAMs
■ Variable port configurations
■ Single-port and simple dual-port modes support for all port widths
■ True dual-port (one read and one write, two reads, or two writes) operation
■ Byte enables for data input masking during writes
■ Two clock-enable control signals for each port (port A and port B)
■ Initialization file to pre-load memory content in RAM and ROM modes
>M9K存储块支持以下功能：
> 每个块拥有8,192个存储位（每个块包括校验位时为9,216位）
> 每个端口独立的读使能（rden）和写使能（wren）信号
> 打包模式，其中M9K存储块被分成两个4.5K单端口RAM
> 可变的端口配置
> 所有端口宽度支持单端口和简单双端口模式
> 真双端口操作（一个读一个写，两个读，或两个写）
> 数据输入屏蔽的字节使能功能，在写入时进行数据输入屏蔽
> 每个端口（A端口和B端口）两个时钟使能控制信号
> 初始化文件，用于在RAM和ROM模式下预加载内存内容

![](Memory-Blocks-in-Cyclone-IV-Devices/summary%20of%20m9k%20memory%20features.png)

# Control Signals (控制信号)
The clock-enable control signal controls the clock entering the input and output
registers and the entire M9K memory block. This signal disables the clock so that the
M9K memory block does not see any clock edges and does not perform any
operations.
The rden and wren control signals control the read and write operations for each port
of M9K memory blocks. You can disable the rden or wren signals independently to
save power whenever the operation is not required.

>时钟使能控制信号控制输入和输出寄存器以及整个M9K存储块的时钟。此信号禁用时钟，使得M9K存储块不会看到任何时钟边沿，也不执行任何操作。
rden和wren控制信号控制M9K存储块每个端口的读和写操作。您可以独立地禁用rden或wren信号，以节省功耗，每当不需要操作时。

# Parity Bit Support (奇偶校验位支持)
Parity checking for error detection is possible with the parity bit along with internal
logic resources. Cyclone IV devices M9K memory blocks support a parity bit for each
storage byte. You can use this bit as either a parity bit or as an additional data bit. No
parity function is actually performed on this bit.
>通过奇偶校验位和内部逻辑资源，可以进行错误检测的奇偶校验。Cyclone IV器件的M9K存储块为每个存储字节支持一个奇偶校验位。您可以将此位用作奇偶校验位或附加数据位。实际上，不会对该位执行奇偶校验功能。

# Byte Enable Support (字节使能支持)
Cyclone IV devices M9K memory blocks support byte enables that mask the input
data so that only specific bytes of data are written. The unwritten bytes retain the
previous written value. The wren signals, along with the byte-enable (byteena)
signals, control the write operations of the RAM block. The default value of the
byteena signals is high (enabled), in which case writing is controlled only by the wren
signals. There is no clear port to the byteena registers. M9K blocks support byte
enables when the write port has a data width of ×16, ×18, ×32, or ×36 bits.
Byte enables operate in one-hot manner, with the LSB of the byteena signal
corresponding to the least significant byte of the data bus. For example, if
byteena = 01 and you are using a RAM block in ×18 mode, data[8..0] is enabled
and data[17..9] is disabled. Similarly, if byteena = 11, both data[8..0] and
data[17..9] are enabled. Byte enables are active high.
>Cyclone IV器件的M9K存储块支持字节使能，用于屏蔽输入数据，以便仅写入特定字节的数据。未写入的字节保留先前写入的值。wren信号与字节使能（byteena）信号一起控制RAM块的写操作。字节ena信号的默认值为高电平（使能），在这种情况下，写入仅由wren信号控制。没有清除端口到字节使能寄存器。当写入端口的数据宽度为×16、×18、×32或×36位时，M9K块支持字节使能。
字节使能以一位热方式工作，其中字节ena信号的最低有效位对应于数据总线的最低有效字节。例如，如果byteena = 01并且您正在使用×18模式的RAM块，则data[8..0]被启用，而data[17..9]被禁用。类似地，如果byteena = 11，则data[8..0]和data[17..9]都被启用。字节使能为高电平有效。

![](Memory-Blocks-in-Cyclone-IV-Devices/Cyclone%20IV%20Devices%20byteena%20Functional%20Waveform.png)
![](Memory-Blocks-in-Cyclone-IV-Devices/byteena%20for%20Cyclone%20IV%20Devices%20M9K%20Blocks.png)

When a byteena bit is deasserted during a write cycle, the old data in the memory
appears in the corresponding data-byte output. When a byteena bit is asserted during
a write cycle, the corresponding data-byte output depends on the setting chosen in
the Quartus® II software. The setting can either be the newly written data or the old
data at that location.
1 Byte enables are only supported for True Dual-Port memory configurations when
both the PortA and PortB data widths of the individual M9K memory blocks are
multiples of 8 or 9 bits
>当在写入周期期间取消assert一个byteena位时，存储器中的旧数据将出现在相应的数据字节输出中。当在写入周期期间assert一个byteena位时，相应的数据字节输出取决于在Quartus® II软件中选择的设置。该设置可以是新写入的数据或该位置处的旧数据。
字节使能仅在True Dual-Port存储器配置中受支持，当单个M9K存储块的PortA和PortB数据宽度都是8位或9位的倍数时。

# Packed Mode Support (支持打包模式)
Cyclone IV devices M9K memory blocks support packed mode. You can implement
two single-port memory blocks in a single block under the following conditions:
■ Each of the two independent block sizes is less than or equal to half of the M9K
block size. The maximum data width for each independent block is 18 bits wide.
■ Each of the single-port memory blocks is configured in single-clock mode. For
more information about packed mode support, refer to “Single-Port Mode” on
page 3–8 and “Single-Clock Mode” on page 3–15.
>支持打包模式
■Cyclone IV器件的M9K存储块支持打包模式。您可以在以下条件下在单个块中实现两个单端口存储块：
两个独立块中的每个块大小都小于或等于M9K块大小的一半。每个独立块的最大数据宽度为18位。
■每个单端口存储块都配置为单时钟模式。有关打包模式支持的更多信息，请参阅“单端口模式”

# Address Clock Enable Support (地址时钟使能支持)
Cyclone IV devices M9K memory blocks support an active-low address clock enable,
which holds the previous address value for as long as the addressstall signal is high
(addressstall = '1'). When you configure M9K memory blocks in dual-port mode,
each port has its own independent address clock enable.
Figure 3–2 shows an address clock enable block diagram. The address register output
feeds back to its input using a multiplexer. The multiplexer output is selected by the
address clock enable (addressstall) signal.
>地址时钟使能支持
Cyclone IV器件的M9K存储块支持主动低电平的地址时钟使能，只要addressstall信号为高（addressstall = '1'），就会保持先前的地址值不变。当您将M9K存储块配置为双端口模式时，每个端口都有自己独立的地址时钟使能。
图3–2显示了地址时钟使能的方块图。地址寄存器的输出通过多路复用器反馈到其输入。多路复用器的输出由地址时钟使能（addressstall）信号选择。

![](Memory-Blocks-in-Cyclone-IV-Devices/Cyclone%20IV%20Devices%20Address%20Clock%20Enable%20Block%20Diagram.png)

The address clock enable is typically used to improve the effectiveness of cache
memory applications during a cache-miss. The default value for the address clock
enable signals is low.
>地址时钟使能通常用于在缓存未命中期间提高缓存存储器应用程序的效率。地址时钟使能信号的默认值为低电平。

![](Memory-Blocks-in-Cyclone-IV-Devices/Cyclone%20IV%20Devices%20Address%20Clock%20Enable%20During%20Read%20Cycle%20Waveform.png)
![](Memory-Blocks-in-Cyclone-IV-Devices/Cyclone%20IV%20Devices%20Address%20Clock%20Enable%20During%20Write%20Cycle%20Waveform.png)

# Mixed-Width Support (混合宽度支持)
M9K memory blocks support mixed data widths. When using simple dual-port, true
dual-port, or FIFO modes, mixed width support allows you to read and write
different data widths to an M9K memory block. For more information about the
different widths supported per memory mode, refer to “Memory Modes” on
page 3–7.
>M9K存储块支持混合数据宽度。在使用简单双端口、真双端口或FIFO模式时，混合宽度支持允许您对M9K存储块读取和写入不同的数据宽度。有关每种内存模式支持的不同宽度的详细信息，请参阅“内存模式”。

# Asynchronous Clear (异步清除)
Cyclone IV devices support asynchronous clears for read address registers, output
registers, and output latches only. Input registers other than read address registers are
not supported. When applied to output registers, the asynchronous clear signal clears
the output registers and the effects are immediately seen. If your RAM does not use
output registers, you can still clear the RAM outputs using the output latch
asynchronous clear feature.
1 Asserting asynchronous clear to the read address register during a read operation
may corrupt the memory content.
>Cyclone IV器件仅支持对读地址寄存器、输出寄存器和输出锁存器进行异步清除。除读地址寄存器以外的输入寄存器不受支持。当应用于输出寄存器时，异步清除信号会清除输出寄存器，并立即产生影响。如果您的RAM不使用输出寄存器，则仍然可以使用输出锁存器的异步清除功能来清除RAM输出。
在读操作期间对读地址寄存器断言异步清除可能会损坏存储器内容。

![](Memory-Blocks-in-Cyclone-IV-Devices/Output%20Latch%20Asynchronous%20Clear%20Waveform.png)

# Memory Modes (存储器模式)
Cyclone IV devices M9K memory blocks allow you to implement fully-synchronous
SRAM memory in multiple modes of operation. Cyclone IV devices M9K memory
blocks do not support asynchronous (unregistered) memory inputs.
M9K memory blocks support the following modes:
■ Single-port
■ Simple dual-port
■ True dual-port
■ Shift-register
■ ROM
■ FIFO
>存储器模式
Cyclone IV器件的M9K存储块允许您在多种操作模式下实现完全同步的SRAM存储器。Cyclone IV器件的M9K存储块不支持异步（未注册）存储器输入。
M9K存储块支持以下模式：
>- 单端口
>- 简单双端口
>- 真双端口
>- 移位寄存器
>- ROM
>- FIFO

## Single-Port Mode (单端口模式)
Single-port mode supports non-simultaneous read and write operations from a single address. Figure 3–6 shows the single-port memory configuration for Cyclone IV devices M9K memory blocks.
![](Memory-Blocks-in-Cyclone-IV-Devices/Single-Port%20Memory.png)
>单端口模式支持从单个地址进行非同时读写操作。图3–6显示了Cyclone IV器件的M9K存储块的单端口存储器配置。

During a write operation, the behavior of the RAM outputs is configurable. If you activate rden during a write operation, the RAM outputs show either the new data being written or the old data at that address. If you perform a write operation with rden deactivated, the RAM outputs retain the values they held during the most recent active rden signal.
To choose the desired behavior, set the Read-During-Write option to either New Data or Old Data in the RAM MegaWizard Plug-In Manager in the Quartus II software. For more information about read-during-write mode, refer to “Read-During-Write Operations” on page 3–15.
>在写操作期间，RAM输出的行为是可配置的。如果在写操作期间激活rden，RAM输出将显示正在写入的新数据或该地址处的旧数据。如果您在未激活rden的情况下执行写操作，则RAM输出将保留它们在最近一次活动rden信号期间持有的值。
为了选择所需的行为，请在Quartus II软件中的RAM MegaWizard插件管理器中将读取期间写入选项设置为New Data或Old Data。有关读取期间写入模式的更多信息，请参阅第3–15页的“读取期间写入操作”。

The port width configurations for M9K blocks in single-port mode are as follow:
■ 8192 × 1
■ 4096 × 2
■ 2048 × 4
■ 1024 × 8
■ 1024 × 9
■ 512 × 16
■ 512 × 18
■ 256 × 32
■ 256 × 36
![](Memory-Blocks-in-Cyclone-IV-Devices/Cyclone%20IV%20Devices%20Single-Port%20Mode%20Timing%20Waveform.png)

## Simple Dual-Port Mode (简单双端口模式)
Simple dual-port mode supports simultaneous read and write operations to different
locations. Figure 3–8 shows the simple dual-port memory configuration.
>简单双端口模式支持对不同位置进行同时读写操作。图3–8显示了简单双端口存储器配置。

![](Memory-Blocks-in-Cyclone-IV-Devices/Cyclone%20IV%20Devices%20Simple%20Dual-Port%20Memory.png)
Cyclone IV devices M9K memory blocks support mixed-width configurations,
allowing different read and write port widths. Table 3–3 lists mixed-width
configurations.
>Cyclone IV器件的M9K存储块支持混合宽度配置，允许不同的读写端口宽度。表3–3列出了混合宽度配置

![](Memory-Blocks-in-Cyclone-IV-Devices/Cyclone%20IV%20Devices%20M9K%20Block%20Mixed-Width%20Configurations%20(Simple%20Dual-Port%20Mode).png)

In simple dual-port mode, M9K memory blocks support separate wren and rden signals. You can save power by keeping the rden signal low (inactive) when not reading. Read-during-write operations to the same address can either output “Don’t Care” data at that location or output “Old Data”. To choose the desired behavior, set the Read-During-Write option to either Don’t Care or Old Data in the RAM MegaWizard Plug-In Manager in the Quartus II software. For more information about this behavior, refer to “Read-During-Write Operations” on page 3–15. Figure 3–9 shows the timing waveform for read and write operations in simple dual-port mode with unregistered outputs. Registering the outputs of the RAM simply delays the q output by one clock cycle.
>在简单双端口模式下，M9K存储块支持单独的wren和rden信号。当不进行读取时，通过保持rden信号低电平（非活动状态）可以节省功耗。对同一地址进行读取期间写入操作时，可以在该位置输出“不关心”数据或输出“旧数据”。要选择所需的行为，请在Quartus II软件中的RAM MegaWizard插件管理器中将读取期间写入选项设置为“不关心”或“旧数据”。有关此行为的更多信息，请参阅第3-15页的“读取期间写入操作”。
图3–9显示了在简单双端口模式下，带有未注册输出的读写操作的时序波形。对RAM的输出进行注册只是将q输出延迟了一个时钟周期。

![](Memory-Blocks-in-Cyclone-IV-Devices/Cyclone%20IV%20Devices%20Simple%20Dual-Port%20Timing%20Waveform.png)

## True Dual-Port Mode (真双端口模式)
True dual-port mode supports any combination of two-port operations: two reads, two writes, or one read and one write, at two different clock frequencies. Figure 3–10 shows Cyclone IV devices true dual-port memory configuration.
>真双端口模式支持两个端口操作的任何组合：两个读操作、两个写操作，或者一个读操作和一个写操作，在两个不同的时钟频率下。图3–10显示了Cyclone IV器件真双端口存储器的配置。

![](Memory-Blocks-in-Cyclone-IV-Devices/Cyclone%20IV%20Devices%20True%20Dual-Port%20Memory.png)
![](Memory-Blocks-in-Cyclone-IV-Devices/Cyclone%20IV%20Devices%20M9K%20Block%20Mixed-Width%20Configurations%20(True%20Dual-Port%20Mode).png)

In true dual-port mode, M9K memory blocks support separate wren and rden signals. You can save power by keeping the rden signal low (inactive) when not reading. Read-during-write operations to the same address can either output “New Data” at that location or “Old Data”. To choose the desired behavior, set the Read-DuringWrite option to either New Data or Old Data in the RAM MegaWizard Plug-In Manager in the Quartus II software. For more information about this behavior, refer to “Read-During-Write Operations” on page 3–15.
>在真双端口模式下，M9K存储块支持单独的wren和rden信号。当不进行读取时，通过保持rden信号低电平（非活动状态），可以节省功耗。对同一地址进行读取期间写入操作时，可以在该位置输出“新数据”或“旧数据”。要选择所需的行为，请在Quartus II软件中的RAM MegaWizard插件管理器中将读取期间写入选项设置为“新数据”或“旧数据”。有关此行为的更多信息，请参阅第3–15页的“读取期间写入操作”。

In true dual-port mode, you can access any memory location at any time from either port A or port B. However, when accessing the same memory location from both ports, you must avoid possible write conflicts. When you attempt to write to the same address location from both ports at the same time, a write conflict happens. This results in unknown data being stored to that address location. There is no conflict resolution circuitry built into the Cyclone IV devices M9K memory blocks. You must handle address conflicts external to the RAM block.
>在真双端口模式下，可以从端口A或端口B的任何时间访问任何存储位置。然而，当从两个端口同时访问同一存储位置时，必须避免可能的写冲突。当尝试同时从两个端口写入相同的地址位置时，会发生写冲突。这导致未知数据被存储到该地址位置。Cyclone IV器件的M9K存储块中没有内置冲突解决电路。您必须在RAM块外部处理地址冲突。

Figure 3–11 shows true dual-port timing waveforms for the write operation at port A and read operation at port B. Registering the outputs of the RAM simply delays the q outputs by one clock cycle.
>图3–11显示了端口A的写操作和端口B的读操作的真双端口时序波形。对RAM的输出进行注册只是将q输出延迟了一个时钟周期。

![](Memory-Blocks-in-Cyclone-IV-Devices/Cyclone%20IV%20Devices%20True%20Dual-Port%20Timing%20Waveform.png)

## Shift Register Mode  ()
Cyclone IV devices M9K memory blocks can implement shift registers for digital signal processing (DSP) applications, such as finite impulse response (FIR) filters, pseudo-random number generators, multi-channel filtering, and auto-correlation and cross-correlation functions. These and other DSP applications require local data storage, traditionally implemented with standard flipflops that quickly exhaust many logic cells for large shift registers. A more efficient alternative is to use embedded memory as a shift register block, which saves logic cell and routing resources.
>Cyclone IV器件的M9K存储块可以实现移位寄存器，用于数字信号处理（DSP）应用，如有限脉冲响应（FIR）滤波器、伪随机数生成器、多通道滤波器以及自相关和互相关函数等。这些和其他DSP应用需要本地数据存储，传统上使用标准触发器实现，但对于大型移位寄存器很快会耗尽许多逻辑单元。更高效的替代方案是使用内置存储作为移位寄存器块，可以节省逻辑单元和布线资源。

The size of a (w × m × n) shift register is determined by the input data width (w), the length of the taps (m), and the number of taps (n), and must be less than or equal to the maximum number of memory bits, which is 9,216 bits. In addition, the size of (w × n) must be less than or equal to the maximum width of the block, which is 36 bits. If you need a larger shift register, you can cascade the M9K memory blocks.
>移位寄存器的大小为（w × m × n），由输入数据宽度（w）、脉冲长度（m）和脉冲数量（n）确定，必须小于或等于最大存储位数，即9216位。此外，（w × n）的大小必须小于或等于块的最大宽度，即36位。如果需要更大的移位寄存器，可以级联M9K存储块。

![](Memory-Blocks-in-Cyclone-IV-Devices/Cyclone%20IV%20Devices%20Shift%20Register%20Mode%20Configuration.png)

## ROM Mode (ROM模式)
Cyclone IV devices M9K memory blocks support ROM mode. A .mif initializes the ROM contents of these blocks. The address lines of the ROM are registered. The outputs can be registered or unregistered. The ROM read operation is identical to the read operation in the single-port RAM configuration.
>Cyclone IV器件的M9K存储块支持ROM模式。一个.mif文件用于初始化这些块的ROM内容。ROM的地址线被注册。输出可以是注册或未注册的。ROM读操作与单端口RAM配置中的读操作相同。

## FIFO Buffer Mode (FIFO缓冲模式)
Cyclone IV devices M9K memory blocks support single-clock or dual-clock FIFO buffers. Dual clock FIFO buffers are useful when transferring data from one clock domain to another clock domain. Cyclone IV devices M9K memory blocks do not support simultaneous read and write from an empty FIFO buffer.
>Cyclone IV器件的M9K存储块支持单时钟或双时钟FIFO缓冲。双时钟FIFO缓冲在从一个时钟域传输数据到另一个时钟域时非常有用。Cyclone IV器件的M9K存储块不支持从空的FIFO缓冲区同时读写。

# Clocking Modes (时钟模式)
Cyclone IV devices M9K memory blocks support the following clocking modes:
■ Independent
■ Input or output
■ Read or write
■ Single-clock
When using read or write clock mode, if you perform a simultaneous read or write to the same address location, the output read data is unknown. If you require the output data to be a known value, use either single-clock mode or I/O clock mode and choose the appropriate read-during-write behavior in the MegaWizard Plug-In Manager.
>Cyclone IV器件的M9K存储块支持以下时钟模式：
■ 独立
■ 输入或输出
■ 读或写
■ 单时钟
当使用读或写时钟模式时，如果同时对相同地址位置进行读或写操作，则输出的读取数据是未知的。如果需要输出数据是已知值，请使用单时钟模式或I/O时钟模式，并在MegaWizard插件管理器中选择适当的读-写行为。

Table 3–5 lists the clocking mode versus memory mode support matrix.
![](Memory-Blocks-in-Cyclone-IV-Devices/Cyclone%20IV%20Devices%20Memory%20Clock%20Modes.png)

## Independent Clock Mode (独立时钟模式)
Cyclone IV devices M9K memory blocks can implement independent clock mode for true dual-port memories. In this mode, a separate clock is available for each port (port A and port B). clock A controls all registers on the port A side, while clock B controls all registers on the port B side. Each port also supports independent clock enables for port A and B registers.
>Cyclone IV器件的M9K存储块可以为真双端口存储器实现独立时钟模式。在此模式下，每个端口（端口A和端口B）都有一个单独的时钟。时钟A控制端口A侧的所有寄存器，而时钟B控制端口B侧的所有寄存器。每个端口还支持端口A和B寄存器的独立时钟使能。

## Input or Output Clock Mode (输入或输出时钟模式)
Cyclone IV devices M9K memory blocks can implement input or output clock mode for FIFO, single-port, true, and simple dual-port memories. In this mode, an input clock controls all input registers to the memory block including data, address, byteena, wren, and rden registers. An output clock controls the data-output registers. Each memory block port also supports independent clock enables for input and output registers.
>Cyclone IV器件的M9K存储块可以为FIFO、单端口、真双端口和简单双端口存储器实现输入或输出时钟模式。在此模式下，输入时钟控制存储块的所有输入寄存器，包括数据、地址、字节使能、写使能和读使能寄存器。输出时钟控制数据输出寄存器。每个存储块端口还支持输入和输出寄存器的独立时钟使能。

##  Read or Write Clock Mode (读或写时钟模式)
Cyclone IV devices M9K memory blocks can implement read or write clock mode for FIFO and simple dual-port memories. In this mode, a write clock controls the data inputs, write address, and wren registers. Similarly, a read clock controls the data outputs, read address, and rden registers. M9K memory blocks support independent clock enables for both the read and write clocks. When using read or write mode, if you perform a simultaneous read or write to the same address location, the output read data is unknown. If you require the output data to be a known value, use either single-clock mode, input clock mode, or output clock mode and choose the appropriate read-during-write behavior in the MegaWizard Plug-In Manager.
>Cyclone IV器件的M9K存储块可以为FIFO和简单双端口存储器实现读或写时钟模式。在此模式下，写时钟控制数据输入、写地址和写使能寄存器。类似地，读时钟控制数据输出、读地址和读使能寄存器。M9K存储块支持读和写时钟的独立时钟使能。
当使用读或写模式时，如果同时对相同地址位置进行读或写操作，则输出的读取数据是未知的。如果需要输出数据是已知值，请使用单时钟模式、输入时钟模式或输出时钟模式，并在MegaWizard插件管理器中选择适当的读-写行为。

## Single-Clock Mode (单时钟模式)
Cyclone IV devices M9K memory blocks can implement single-clock mode for FIFO, ROM, true dual-port, simple dual-port, and single-port memories. In this mode, you can control all registers of the M9K memory block with a single clock together with clock enable.
>Cyclone IV器件的M9K存储块可以为FIFO、ROM、真双端口、简单双端口和单端口存储器实现单时钟模式。在此模式下，您可以使用单时钟和时钟使能控制M9K存储块的所有寄存器。