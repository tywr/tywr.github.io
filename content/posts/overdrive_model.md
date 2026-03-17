---
title: "How I modeled my favourite overdrive pedal using C++"
date: 2026-03-17
summary: "I modeled and programmed a software recreation of my favourite bass-guitar overdrive pedal so I can use the software as a my personal live pedalboard."
math: true
tags: ["programming", "dsp", "juce", "c++", "bass-guitar"]
---

I have been playing bass guitar for around a decade. I developed this condition called GAS – Gear Acquisition Syndrome, quite common for musicians. At some point, it becomes easier to pay for new gear and feel the consumption thrill, than to sit down and practise. That's how I acquired my favourite bass pedal overdrive pedal, the Darkglass Vintage Microtubes, a CMOS-based overdrive ! It's a very iconic bass pedal that recreates the feeling of an overdriven vintage amp. It's been on my pedalboard ever since as my always on pedal.

## The problem

Analog devices are nice, but they also require space and money. For most of my practice sessions, I actually found myself plugging my bass directly into my sound card, and using a software to emulate the amp sound. It was the most convenient way for me to practice, plug the guitar, open the software and practice.

I bought a software to do the amp emulation on my laptop, one emulating my favorite pedal : the Darkglass Ultra from NeuralDSP. For some reason, I never really settled with it. The sound was not as organic as my analog pedal, and I wanted to be able to do some more things like adding compression and chorus onto the signal. At the same time, I didn't want to open a DAW (Digital Audio Workstation) to add extra plugins. I liked the idea of using a single software for my practice session. That's how I decided to code my own software, that would bundle together the amp emulation, the compression and the chorus effects.

## Coding an audio software

The most well known open-source framework for coding such softwares is called Juce and uses C++. I had learnt C++ during my studies, so nothing too hard to setup. I won't dive into the details, but setting up an audio application is actually straightforward, and some boilerplate was actually enabling me to create a software to directly stream the sound from my soundcard into my headphones. Now, I needed to write the actual algorithm to transform the audio buffer coming from the input into a processed signal. For the compressor and chorus effects, I used standards algorithms and adjusted them to my taste, but I did nothing fancy on this part. For the overdrive part that's another story, but I'll try to explain.

## Overdriving a signal

The very first overdriven tones came from damaged or faulty amplifiers. Amplifier tubes would sometimes malfunction – either through age, damage, or being pushed beyond their design limits — causing the signal to clip (flatten the peaks of the sine wave), producing a harmonically rich, distorted sound. Early blues and rock & roll players noticed this sounded good and began intentionally recreating it.

The core of an overdrive or saturation effect is a waveshaper – a function that maps an input amplitude to an output amplitude non-linearly. The most commonly used is the hyperbolic tangent :

$$w(x) = \tanh(kx) = \frac{e^x - e^{-x}}{e^x + e^{-x}}$$

where $k$ controls the drive amount. At low drive the curve is nearly linear; as $k$ increases the output saturates and harmonics are introduced.

Any function $w$ can be used, and the shape of the function is gonna dictate which new harmonics are gonna be added into the signal. For overdrive and saturation, the waveshaper will flatten out the input peaks to a capped value, giving plenty of new harmonics and natural compression.

## Modeling the Vintage Microtubes signal chain

To model my Vintage Microtubes pedal, I looked into the electronics. To my surprise, I was able to find quite a few schematics of the wiring on different forums. It is then possible to analyze the electrical components and figure out the different filters (HPF, LPF, T-notch etc.) and the non-linear elements being applied to the input signal as it passed through the pedal. In this model, a CMOS chip is being overdriven.

The structure of the signal processing looks like the following:

$$
\text{Input} \rightarrow \text{Filter}_1 \rightarrow \text{Filter}_2 \rightarrow ... \rightarrow \text{CMOS} \rightarrow \text{Filter}_N \rightarrow ... \rightarrow \text{Output}
$$

Based on the $R$ and $C$ values from the schematics, you can usually determine the filter parameters. With the juce framework, it is then really straightforward to apply every single filter to the input signal.

The only real unknown part, is then to determine the waveshaper function of the non-linear element, the CMOS device.

## CMOS device model

1. Naive physical model - not that well sounding
2. Mention the research paper
3. Explain the model being used
4. Explain how to compute the transfer curve
5. Explain how to use it inside the software
6. Et voilà
