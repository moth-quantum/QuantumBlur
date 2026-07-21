# QuantumBlur

The original README, relevant links such as the paper and the blog post and the library description can be all found [here](https://github.com/moth-quantum/QuantumBlur/tree/main).

This specific branch supports C# implementation of Quantum Blur. Its supplement library is [MicroMoth], that can be found [here](https://github.com/moth-quantum/MicroMoth) as a GitHub repository, and [here](https://www.nuget.org/packages/Moth.MicroMoth) as an official NuGet release. (NET 8.0+) This is not the direct descendent of the old [Unity implementation](https://github.com/TigrisCallidus/QuantumBlurUnity/blob/master/README.md) but built with the totally different purpose. This release does not ship the specific plugin but the library itself, so that people with Unity can download `.dll` and Godot users can natively install the package with `dotnet package add`. Furthermore, this C# implementation uses the C# version of MicroMoth, the world's smallest quantum emulation library, thus the user can expect relatively fast computational result. (approx. 2 seconds for 2048x2048 2D image)

## Requirements
TBD

## Installation

TBD

## How to use

TBD