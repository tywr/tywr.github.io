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

## Overdrive and waveshapers

The very first overdriven tones were, like most interesting discoveries, accidental. Amplifier tubes would malfunction — through age, rough handling, or simply being pushed past what they were designed to handle — causing the signal to clip: the peaks of the sound wave would flatten, and in doing so, produce something harmonically richer and more interesting than the original. Early blues and rock & roll players noticed this, recognized it for what it was worth, and began reproducing it deliberately. The rest, as they say, followed.
At the technical core of any overdrive or saturation effect sits a waveshaper — a function that takes an input amplitude and returns an output amplitude, but not in a straight line. The most commonly used is the hyperbolic tangent:

$$w(x) = \tanh(kx)$$

where $k$ controls the drive amount. At low drive, the curve is nearly linear and the effect is subtle; as $k$ increases, the output begins to saturate and harmonics emerge. It is a simple function, which is part of why it works so well.

Any function $w$ will do, in principle – the shape of the curve is what determines which new harmonics get introduced into the signal. For overdrive and saturation specifically, the waveshaper flattens the peaks of the input down to a capped value. This produces a generous amount of new harmonics and a natural compression of the sound.



## Modeling the Vintage Microtubes signal chain

To model my Vintage Microtubes pedal digitally, I did what any reasonable person would do: study how the real hardware actually works, rather than guessing, which tends to produce mediocre results.

As it turns out, other enthusiasts had already taken the trouble of sharing detailed circuit diagrams on various forums. This is one of the more quietly useful things the internet facilitates, and it saved me a considerable amount of time.

These diagrams reveal, with the clarity that electronics always afford, exactly what happens to your audio signal as it moves through the pedal. It passes through a series of filters — components that selectively boost or cut certain frequency ranges — before and after reaching the core distortion stage. Filters are the pedal's tone-shaping components. Some cut low frequencies. Some cut highs. One carves a very specific notch out of the spectrum, which turns out to matter quite a bit for the overall character of the sound. The signal flow is not complicated and can be summarized as the following :

$$
\text{Input} \rightarrow \text{Filter}_1 \rightarrow \text{Filter}_2 \rightarrow ... \rightarrow \text{CMOS} \rightarrow \text{Filter}_N \rightarrow ... \rightarrow \text{Output}
$$

Recreating the filters digitally is the straightforward part. The circuit diagrams include the exact values of every resistor and capacitor, and from those numbers the filter behavior follows mathematically. The JUCE audio framework then handles the implementation cleanly — this is the kind of problem it was designed for.

The CMOS chip is a different matter, and the more interesting one. It is a small electronic component that, when driven beyond its intended operating range, produces distortion — the harmonic grit that defines the pedal's personality. Unlike the filters, which behave in an orderly, linear fashion, the CMOS distorts the signal in ways that resist simple mathematical description. Pinning down the precise function that captures this behavior — the so-called waveshaper function — is the real problem.

Based on the $R$ and $C$ values from the schematics, you can usually determine the filter parameters. With the juce framework, it is then really straightforward to apply every single filter to the input signal.

## A naive CMOS model

The good news is you can usually find the transfer curve - or the waveshaper function – appearance in the technical notice of the chip, in our case the CD4049. The bad news is that it doesn't come with a ready to use equation to write into the plugin. We'll need to find some equations for that.

For modeling purposes, the Shichman-Hodges model is often used, using a square law approximation. A CMOS device consists of two transistors, a NMOS and PMOS, each giving saturation for different input values. Here the goal is not give all the details, but the model can give us the piecewise functions over different zones.

In our case we're trying to get the output value of the voltage $V_{out}$ based on the input voltage $V_{in}$. This function can be called transfer function, but it is also the waveshaper function that we are interested in.

$$
V_{out} = \begin{cases}
V_{DD} & (V_{in} < V_{th,n}) \\
\frac{\left(1 + R_L \cdot k'_n \cdot \frac{W_n}{L_n} \cdot (V_{in} - V_{th,n})\right) - \sqrt{\left(1 + R_L \cdot k'_n \cdot \frac{W_n}{L_n} \cdot (V_{in} - V_{th,n})\right)^2 - 2 R_L \cdot k'_n \cdot \frac{W_n}{L_n} \cdot V_{DD}}}{R_L \cdot k'_n \cdot \frac{W_n}{L_n}} & (V_{th,n} \leq V_{in} < V_{DD}/2) \\
\frac{k'_n}{2} \cdot \frac{W_n}{L_n} \cdot (V_{in} - V_{th,n})^2 = \frac{k'_p}{2} \cdot \frac{W_p}{L_p} \cdot (V_{in} - V_{DD} - V_{th,p})^2 & (V_{in} \approx V_{DD}/2) \\
\frac{\left(1 + R_L \cdot k'_p \cdot \frac{W_p}{L_p} \cdot (V_{in} - V_{DD} - V_{th,p})\right) - \sqrt{\left(1 + R_L \cdot k'_p \cdot \frac{W_p}{L_p} \cdot (V_{in} - V_{DD} - V_{th,p})\right)^2 - 2 R_L \cdot k'_p \cdot \frac{W_p}{L_p} \cdot V_{DD}}}{R_L \cdot k'_p \cdot \frac{W_p}{L_p}} & (V_{DD}/2 < V_{in} \leq V_{DD} + V_{th,p}) \\
0 & (V_{in} > V_{DD} + V_{th,p})
\end{cases}
$$

It looks ugly, but nothing too hard to solve with a Newton-Raphson method.


1. Naive physical model - not that well sounding
2. Mention the research paper
3. Explain the model being used
4. Explain how to compute the transfer curve
5. Explain how to use it inside the software
6. Et voilà
