---
title: "How I modeled my favourite overdrive pedal using C++"
date: 2026-03-17
summary: "I modeled and programmed a software recreation of my favourite bass-guitar overdrive pedal so I can use the software as a my personal live pedalboard."
math: true
plot: true
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

As it turns out, other enthusiasts had already taken the trouble of sharing detailed circuit diagrams on various forums. This is one thing the internet facilitates, and it saved me a considerable amount of time.

These diagrams reveal exactly what happens to your audio signal as it moves through the pedal. It passes through a series of filters — components that selectively boost or cut certain frequency ranges — before and after reaching the core distortion stage. Filters are the pedal's tone-shaping components. Some cut low frequencies. Some cut highs. One carves a very specific notch out of the spectrum, which turns out to matter quite a bit for the overall character of the sound. The signal flow is not complicated and can be summarized as the following :

$$
\text{Input} \rightarrow \text{Filter}_1 \rightarrow \text{Filter}_2 \rightarrow ... \rightarrow \text{CMOS} \rightarrow \text{Filter}_N \rightarrow ... \rightarrow \text{Output}
$$

Recreating the filters digitally is the straightforward part. The circuit diagrams include the exact values of every resistor and capacitor, and from those numbers the filter behavior follows mathematically. The JUCE audio framework then handles the implementation cleanly — this is the kind of problem it was designed for.

The CMOS chip is a different matter, and the more interesting one. It is a small electronic component that, when driven beyond its intended operating range, produces distortion — the harmonic grit that defines the pedal's personality. Unlike the filters, which behave in an orderly, linear fashion, the CMOS distorts the signal in ways that resist simple mathematical description. Pinning down the precise function that captures this behavior — the so-called waveshaper function — is the real problem.

## The standard CMOS model

The transfer curve — or waveshaper function — can usually be found in the datasheet of the chip, in this case the CD4049. It does not come with a ready-to-use equation, so one needs to be derived.For modeling purposes, the Shichman-Hodges model is commonly used, based on a square law approximation. A CMOS device consists of two transistors, an NMOS and a PMOS, each conducting over different input voltage ranges. The model yields piecewise functions over distinct operating zones. In both transistors, the current $I_{DS}$ controlled by two voltages: $V_{GS}$ the voltage between gate and source which controls whether the transistor conducts, and $V_{DS}$, the voltage between drain and source across which the current flows. Each transistor has a threshold $V_{th}$. For clarity, we use the conventions $nmos=n$ and $pmos=p$.

$$
I_{DS,n} = \begin{cases}
0 & (V_{GS} \leq V_{th,n}) \\
k_n \left[ (V_{GS} - V_{th,n}) V_{DS} - \dfrac{V_{DS}^2}{2} \right] & (V_{GS} > V_{th,n},\ V_{DS} < V_{GS} - V_{th,n}) \\
\dfrac{k_n}{2} (V_{GS} - V_{th,n})^2 (1 + \delta \cdot V_{DS}) & (V_{GS} > V_{th,n},\ V_{DS} \geq V_{GS} - V_{th,n})
\end{cases}
$$

$$
I_{DS,p} = \begin{cases}
0 & (V_{GS} \geq V_{th,p}) \\
-k_p \left[ (V_{GS} - V_{th,p}) V_{DS} - \dfrac{V_{DS}^2}{2} \right] & (V_{GS} < V_{th,p},\ V_{DS} \geq V_{GS} - V_{th,p}) \\
-\dfrac{k_p}{2} (V_{GS} - V_{th,p})^2 (1 + \delta \cdot V_{DS}) & (V_{GS} < V_{th,p},\ V_{DS} < V_{GS} - V_{th,p})
\end{cases}
$$

Each zone can be implemented directly in code. The output voltage $V_{out}$ then found by solving KCL at the output node, using a Newton-Raphson method with the conductances $G_{x} = dI_{x} / dV_{x}$ as the derivative term.

Here is what a solver with python could look like:

```python
class CMOS_SH:

    def __init__(self):
        self.V_dd = 9.0
        self.kn = 1.0e-3
        self.vth_n = 0.5
        self.kp = 0.4e-3
        self.vth_p = -0.5
        self.delta = 0.06

    def nmos(self, vgs, vds):
        vt = self.vth_n
        if vgs <= vt:
            return 0.0, 0.0
        if vds < vgs - vt:
            ids = self.kn * (vgs - vt - vds / 2) * vds
            gds = self.kn * (vgs - vt) - self.kn * vds
            return ids, gds
        ids = 0.5 * self.kn * (vgs - vt) ** 2 * (1 + self.delta * vds)
        gds = 0.5 * self.kn * (vgs - vt) ** 2 * self.delta
        return ids, gds

    def pmos(self, vgs, vds):
        vt = self.vth_p
        if vgs >= vt:
            return 0.0, 0.0
        if vds >= vgs - vt:
            ids = -self.kp * (vgs - vt - vds / 2) * vds
            gds = -self.kp * (vgs - vt) + self.kp * vds
            return ids, gds
        ids = -0.5 * self.kp * (vgs - vt) ** 2 * (1 + self.delta * vds)
        gds = -0.5 * self.kp * (vgs - vt) ** 2 * self.delta
        return ids, gds

    def solve(self, vin: float) -> float:
        vout = self.V_dd / 2
        for _ in range(10):
            vgs_n, vds_n = vin, vout
            vgs_p, vds_p = vin - self.V_dd, vout - self.V_dd
            ids_n, gds_n = self.nmos(vgs_n, vds_n)
            ids_p, gds_p = self.pmos(vgs_p, vds_p)

            f_x = ids_n + ids_p
            f_prime_x = gds_n + gds_p

            # Add a small dampening factor to ensure stability of the solving
            vout = vout - f_x / (f_prime_x + 1e-3)
            vout = np.clip(vout, 0, self.V_dd)
        return vout
```

And this is what the transfer curve would look like after solving the equations and rescaling it:

{{< plot "figure1" >}}
  {
    "data": [
      {"x": [0.0, 0.09090909090909091, 0.18181818181818182, 0.2727272727272727, 0.36363636363636365, 0.4545454545454546, 0.5454545454545454, 0.6363636363636364, 0.7272727272727273, 0.8181818181818182, 0.9090909090909092, 1.0, 1.0909090909090908, 1.1818181818181819, 1.2727272727272727, 1.3636363636363638, 1.4545454545454546, 1.5454545454545454, 1.6363636363636365, 1.7272727272727273, 1.8181818181818183, 1.9090909090909092, 2.0, 2.090909090909091, 2.1818181818181817, 2.272727272727273, 2.3636363636363638, 2.4545454545454546, 2.5454545454545454, 2.6363636363636362, 2.7272727272727275, 2.8181818181818183, 2.909090909090909, 3.0, 3.090909090909091, 3.181818181818182, 3.272727272727273, 3.3636363636363638, 3.4545454545454546, 3.5454545454545454, 3.6363636363636367, 3.7272727272727275, 3.8181818181818183, 3.909090909090909, 4.0, 4.090909090909091, 4.181818181818182, 4.2727272727272725, 4.363636363636363, 4.454545454545455, 4.545454545454546, 4.636363636363637, 4.7272727272727275, 4.818181818181818, 4.909090909090909, 5.0, 5.090909090909091, 5.181818181818182, 5.2727272727272725, 5.363636363636364, 5.454545454545455, 5.545454545454546, 5.636363636363637, 5.7272727272727275, 5.818181818181818, 5.909090909090909, 6.0, 6.090909090909091, 6.181818181818182, 6.2727272727272725, 6.363636363636364, 6.454545454545455, 6.545454545454546, 6.636363636363637, 6.7272727272727275, 6.818181818181818, 6.909090909090909, 7.0, 7.090909090909091, 7.181818181818182, 7.272727272727273, 7.363636363636364, 7.454545454545455, 7.545454545454546, 7.636363636363637, 7.7272727272727275, 7.818181818181818, 7.909090909090909, 8.0, 8.090909090909092, 8.181818181818182, 8.272727272727273, 8.363636363636363, 8.454545454545455, 8.545454545454545, 8.636363636363637, 8.727272727272727, 8.818181818181818, 8.90909090909091, 9.0], "y": [8.999999726863882, 8.999999701580796, 8.999999673689384, 8.999999642892067, 8.999999608853958, 8.999999571197751, 8.999499522988408, 8.995446944365607, 8.987202861743382, 8.9746126602417, 8.957510467543148, 8.935717689392211, 8.909041297855541, 8.877271819033723, 8.840180952717185, 8.797518737724861, 8.74901015161979, 8.694350999654493, 8.633202901480754, 8.565187119872727, 8.489876885115581, 8.406787738875812, 8.315365231818797, 8.214969026760343, 8.104852028393145, 7.984132486611351, 7.8517559344582875, 7.706442012410423, 7.5466080976064465, 7.370255980567295, 7.174796983319096, 6.956768793744132, 6.711348451030142, 6.431446600038198, 6.105835073386023, 5.7146404417492365, 5.2155426866594565, 4.4766204109319006, 1.1225052283847676, 1.0044039748353548, 0.9071424869961854, 0.8244926155657437, 0.7528160644200866, 0.6897340737273646, 0.6336402633387096, 0.5833325460232364, 0.5379227173012103, 0.4966908825542638, 0.4590752552063438, 0.424621216613093, 0.39295527592382085, 0.3637665838942143, 0.3367934918796404, 0.3118135744889391, 0.28863608779126615, 0.2670961765493239, 0.24705036107983958, 0.22837297599340278, 0.21095332763867564, 0.1946934015383844, 0.17950599587063498, 0.16531318866693376, 0.15204506907578694, 0.13963867953614464, 0.1280371278593651, 0.11718883728120039, 0.10704690937751425, 0.09756857994072006, 0.08871475191428206, 0.08044959258537347, 0.07274018466221896, 0.06555622277486771, 0.05886974845604216, 0.05265491787182623, 0.04688779754770495, 0.04154618412505241, 0.03660944482575519, 0.03205837582845352, 0.027875076192317216, 0.02404283532165701, 0.020546032261397677, 0.0173700453608863, 0.014501171050726807, 0.011926550651557526, 0.009634104280730702, 0.007612471047409479, 0.00585095483247443, 0.00433947503993078, 0.003068521783768723, 0.0020291150405379573, 0.001212767354974866, 0.0006114497352909438, 0.00021756041737921466, 2.389621420650526e-05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "type": "scatter", "name": "Series A"},
    ],
    "layout": {
      "title": "CMOS Transfer Curve",
      "yaxis": {"title": "Output Voltage (V)"},
      "xaxis": {"title": "Input Voltage (V)"}
    }
  }
{{< /plot >}}

From there, a c++ solver can be implemented in the same way. The function is then rescaled to output values between -1 and 1, and loaded into a lookup table, so that the software can compute it quickly for every incoming sample from the input audio buffer.

For some reason, this waveshaper didn't sound really good. It's hard to pinpoint what didn't work out there, but it might highly be because of the sharp nature of the curve, introducing an unpleasant amount of aliasing into the output signal.


## Refining the model

It turns out some researchers in the field were also interested about modeling the same device as me, but another pedal : the Red Llama, which uses the same chip for overdriving the signal. What a luck.

The original paper can be found [there](https://www.dafx.de/paper-archive/2020/proceedings/papers/DAFx2020_paper_21.pdf).

Instead of using the raw model exposed in the previous section, they opted for measuring the device itself, and fitting a smooth polynomial curve. The paper suggests to introduce the following coefficients into the model previously presented. It would be equivalent to overwriting the functions `nmos` and `pmos` in the solver, and changing a few parameters.

```python
    def nmos(self, vgs, vds):
        """Calculates NMOS I_ds and its derivative w.r.t. vds (g_ds)."""
        vt_coef = [1.208306917691355, 0.3139084341943607]
        alpha_coef = [0.020662094888127674, -0.0017181795239085821]

        alpha = alpha_coef[1] * vgs + alpha_coef[0]
        vt = vt_coef[1] * vgs + vt_coef[0]

        if vgs <= vt:
            return 0.0, 0.0, vt, alpha

        if vds < vgs - vt and vgs > vt:
            ids = alpha * (vgs - vt - vds / 2) * vds
            gds = alpha * (vgs - vt) - alpha * vds  # Derivative d(Ids)/d(Vds)
            return ids, gds, vt, alpha

        ids = 0.5 * alpha * (vgs - vt) ** 2
        gds = 0.0
        return ids, gds, vt, alpha

    def pmos(self, vgs, vds):
        """Calculates PMOS I_sd and its derivative w.r.t. vsd (g_sd)."""
        vt_coef = [-0.25610349392710086, 0.27051216771368214]
        alpha_coef = [
            -0.0003577445606469842,
            -0.0008620153809796321,
            -0.00016848836814836602,
            -1.0800821774906936e-5,
        ]
        alpha = (
            alpha_coef[3] * vgs**3
            + alpha_coef[2] * vgs**2
            + alpha_coef[1] * vgs
            + alpha_coef[0]
        )
        vt = vt_coef[1] * vgs + vt_coef[0]

        if vgs >= vt:
            return 0.0, 0.0, vt, alpha

        if vds >= vgs - vt and vgs < vt:
            ids = -alpha * (vgs - vt - vds / 2) * vds * (1 - self.delta * vds)
            gds = -alpha * (
                3 * self.delta * vds**2 / 2
                - (2 * self.delta * (vgs - vt) + 1) * vds
                + vgs
                - vt
            )
            return ids, gds, vt, alpha

        ids = -0.5 * alpha * ((vgs - vt) ** 2) * (1 - self.delta * vds)
        gds = 0.5 * alpha * self.delta * (vgs - vt) ** 2
        return ids, gds, vt, alpha
```

After solving the equations with those new expressions, we can then plot the rescaled transfer function :

{{< plot "figure2" >}}
  {
    "data": [
      {"x": [-1.8, -1.7303030303030305, -1.6606060606060606, -1.590909090909091, -1.5212121212121212, -1.4515151515151516, -1.3818181818181818, -1.3121212121212122, -1.2424242424242427, -1.1727272727272728, -1.103030303030303, -1.0333333333333334, -0.9636363636363638, -0.8939393939393941, -0.8242424242424244, -0.7545454545454546, -0.684848484848485, -0.6151515151515154, -0.5454545454545456, -0.47575757575757605, -0.40606060606060623, -0.33636363636363664, -0.26666666666666683, -0.19696969696969724, -0.12727272727272765, -0.057575757575757835, 0.012121212121211755, 0.08181818181818157, 0.15151515151515116, 0.22121212121212097, 0.2909090909090908, 0.36060606060606015, 0.43030303030302997, 0.4999999999999998, 0.5696969696969691, 0.639393939393939, 0.7090909090909088, 0.7787878787878786, 0.848484848484848, 0.9181818181818178, 0.9878787878787876, 1.057575757575757, 1.1272727272727268, 1.1969696969696966, 1.2666666666666664, 1.3363636363636358, 1.4060606060606056, 1.4757575757575754, 1.5454545454545447, 1.6151515151515146, 1.6848484848484844, 1.7545454545454542, 1.8242424242424236, 1.8939393939393934, 1.9636363636363632, 2.033333333333333, 2.1030303030303026, 2.172727272727272, 2.242424242424242, 2.3121212121212116, 2.381818181818182, 2.451515151515151, 2.5212121212121206, 2.590909090909091, 2.66060606060606, 2.7303030303030296, 2.8, 2.869696969696969, 2.9393939393939386, 3.009090909090909, 3.078787878787878, 3.1484848484848484, 3.218181818181818, 3.287878787878787, 3.3575757575757574, 3.427272727272727, 3.496969696969696, 3.5666666666666664, 3.636363636363636, 3.706060606060605, 3.7757575757575754, 3.845454545454545, 3.915151515151514, 3.9848484848484844, 4.054545454545454, 4.124242424242424, 4.193939393939393, 4.263636363636363, 4.333333333333333, 4.403030303030302, 4.472727272727272, 4.542424242424242, 4.612121212121211, 4.681818181818181, 4.751515151515151, 4.82121212121212, 4.89090909090909, 4.96060606060606, 5.030303030303029, 5.1], "y": [-1.0, -1.0, -0.9998720977798139, -0.9984461398931457, -0.9954003872313106, -0.9906851455004453, -0.9842494441988596, -0.9760399214426347, -0.9659994225051842, -0.9540652380726735, -0.940166878052396, -0.9242232312832575, -0.9061388916469484, -0.8857993213761004, -0.8630643453283566, -0.8377591749889268, -0.809661650368823, -0.7784834638090468, -0.7438413655009815, -0.7052107586484324, -0.6618461734133498, -0.6126337902557291, -0.5557872808406277, -0.4881164709011392, -0.402773242996447, -0.2775682838859881, 0.08250539142365687, 0.577868098187309, 0.7855219300523901, 0.81562768107495, 0.8354027955054977, 0.8504713494355297, 0.8627252820725001, 0.87307168969161, 0.8820268770476771, 0.8899168286596436, 0.8969622943921738, 0.9033205206086498, 0.9091078909618975, 0.9144131658028262, 0.919305686930993, 0.923840703900225, 0.928062965732239, 0.932009221067703, 0.9357100059977645, 0.9391909524598763, 0.9424737652256927, 0.9455769644216391, 0.9485164587441103, 0.9513059941891769, 0.9539575097616071, 0.9564814226602586, 0.9588868592922728, 0.9611818441808884, 0.9633734557900481, 0.965467956098562, 0.9674708991573299, 0.969387222680682, 0.9712213258383993, 0.9729771357462389, 0.974658164642134, 0.9762675593416973, 0.9778081442607898, 0.9792824590532878, 0.9806927917230922, 0.9820412079191853, 0.9833295770024503, 0.9845595953764199, 0.9857328074961204, 0.9868506249058843, 0.9879143436054555, 0.9889251600016199, 0.9898841856681558, 0.9907924611087299, 0.9916509686943368, 0.9924606449281432, 0.9932223921754547, 0.9939370899844325, 0.9946056061137265, 0.9952288073760301, 0.9958075704014492, 0.9963427924213194, 0.9968354021715892, 0.9972863710150056, 0.9976967243830879, 0.9980675536422299, 0.9984000284933097, 0.9986954100209745, 0.9989550645174583, 0.9991804782165562, 0.9993732730864628, 0.9995352238458785, 0.9996682763864667, 0.9997745678068689, 0.9998564482895855, 0.9999165050828154, 0.9999575888856036, 0.9999828429773936, 0.9999957354835284, 1.0], "type": "scatter", "name": "Series A"},
    ],
    "layout": {
      "title": "CMOS Transfer Curve",
      "yaxis": {"title": "Normalized Output Voltage"},
      "xaxis": {"title": "Biased Input Voltage (V)"}
    }
  }
{{< /plot >}}

Again, the curve will be normalized and loaded into a lookup table so it can be quickly applied on incoming sample from the input audio buffer. This time the sound coming out of it feels a lot more organic and less digital. It's still not quite like the analog version, but it's definitely good enough for my tastes ! 


## Conclusion

If you're curious about finding out how this sounds, you can download it from the repository [there](https://github.com/tywr/orbital-bass-engine). It's open-source and free to use !

In the end, the waveshaper part of the sound is not necessarily what affects the most the overall vibe or the sound, but it gives character based on the amount of new harmonics that it brings. A smooth curve will add gentle harmonics, while hard limiter will introduce a lot of harmonics.

To me it seems that most of pedal character comes from a careful choice of the filters that are coming before and after the waveshaping, way more than the waveshaper function itself.
