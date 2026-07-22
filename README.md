# QuantumBlur

The original README, relevant links such as the paper and the blog post and the library description can be all found [here](https://github.com/moth-quantum/QuantumBlur/tree/main).

This branch is the C# implementation of Quantum Blur. Its companion library is [MicroMoth](https://github.com/moth-quantum/MicroMoth) — available as a [GitHub repository](https://github.com/moth-quantum/MicroMoth) and an [official NuGet release](https://www.nuget.org/packages/Moth.MicroMoth) targeting **.NET 8.0 (Godot) and .NET Standard 2.1 (Unity)**.

This is not a descendant of the old [Unity implementation](https://github.com/TigrisCallidus/QuantumBlurUnity/blob/master/README.md). This release ships the library itself rather than an engine plugin, so Godot users install it natively with `dotnet add package Moth.QuantumBlur`, and Unity users can add it via NuGetForUnity (or drop in the `netstandard2.1` `.dll`). It builds on the C# port of MicroMoth, a very small quantum-emulation library, so results are fast; approximately 2–3 seconds for a 2048x2048 image.

## Requirements
TBD

## Installation

**Godot / .NET:**
```bash
dotnet add package Moth.QuantumBlur
```
This pulls in `Moth.MicroMoth` automatically.

**Unity:** install `Moth.QuantumBlur` via [NuGetForUnity](https://github.com/GlitchEnzo/NuGetForUnity), or copy the `netstandard2.1` DLLs of both `Moth.QuantumBlur` and `Moth.MicroMoth` into your `Assets/` folder.

## How to use

TBD