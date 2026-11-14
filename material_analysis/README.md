# Handover: AI Material Moisture Analysis

Fact-checked 2026-11-14. Corrections applied inline; see fact_check.md for verdicts and sources.

## Goal

Build a non-contact system that estimates moisture % of bulk materials (coal, limestone, iron ore, sinter) on conveyors from thermal camera images, modeled on Ripik.ai Material Moisture Analysis.

- How Ripik does it: "advanced infrared cameras" (no model or spec given) at tippler point, crushers, conveyor belts and kiln feed areas; infrared cameras plus AI estimate moisture in real time. Materials listed on the page: coal, coke, sinter, iron ore, limestone, clinker, bauxite, fly ash.
- Where Ripik uses AI (model types not disclosed, so inferred): temperature-to-moisture regression, per-material calibration, anomaly detection (blockages, clumping).
  - Ripik states DCS/SCADA integration (stated, not inferred).
  - Ripik says the same Vision AI "can be extended" to detect foreign objects, oversized lumps and conveyor anomalies. Blockage/clumping risk from high moisture is mentioned.
- Not AI: pixel temperatures (camera calibration), color display palette, threshold alerts.
- No numeric accuracy figure is published for the moisture product (only "accurate measurements" claims).

## Data

Public data is scarce; plan to collect your own.

- IEEE DataPort "Iron Ore Powder Dataset" (DOI 10.21227/5gcj-hx24): images of iron ore powder, not thermal. License CC BY 4.0, login required to download, one 1.53 GB zip (image_3000.zip). Moisture levels are not specified on the page. The page does not say "RGB" but describes photos/texture (RGB is inferred).
- Reference papers (methods, no data):
  - Coal surface moisture via online image processing: Choudhary et al. (2020), J. Min. Metall. Sect. A 56A(1):37-46. Visible-light images of a coal bed on a conveyor every 30 min; reflectivity/intensity correlates with moisture; Tata Steel Long Products sponge-iron kiln.
  - Iron ore green pellet moisture: Zhou S.-y., Liu X.-y. (authors per Crossref, unverified against the paper) (2023), J. Iron Steel Res. Int. 30(5):851-863.
  - Image-based coal characterization: Gorai et al. (2021), Int J Coal Sci Technol 8(4):737-755. Moisture R² 0.84 (confirmed; ANN on RGB images, 280 texture features, 80 calibration samples; whether 0.84 is calibration or test is unclear). Also 0.89 fixed carbon, 0.92 ash, 0.92 volatile matter.
- Lab rig: oven-dry samples, add measured water (e.g. 2-16%), image under controlled conditions.
- Plant data: grab belt samples time-synced to frames; ground truth by loss on drying. Target several hundred to a few thousand pairs across seasons and shifts. Standards:
  - Coal: ISO 589:2008 "Hard coal - Determination of total moisture".
  - Iron ore: ISO 3087:2020 "Iron ores - Determination of the moisture content of a lot".
  - India coal: IS 1350 (Part 1) proximate analysis (current edition unverified; a 2025 revision is listed).
- Log alongside each frame: air temperature, humidity, wind/belt speed, layer depth.

## Physics: temperature to moisture

No universal formula; use physics to build features, then calibrate on lab samples.

1. Surface energy balance. Incoming heat drives evaporation; water activity ($a_w$, via a GAB sorption isotherm) sets the evaporation rate. Solve for $a_w$ from surface temperature, air temperature, humidity and air speed, then invert the isotherm.

   $$h\,(T_{air}-T_s) + q_{rad,net} = \dot m_{evap} L + G, \quad \dot m_{evap} = h_m\left(\rho_{v,s}(T_s,a_w) - \rho_{v,air}\right)$$

   - $G$ is conduction into the bed. $q_{rad,net}$ = absorbed solar + net longwave.
   - $L \approx 2.45$ MJ/kg at about 20 °C (about 2.50 at 0 °C, 2.26 at 100 °C).
   - GAB isotherm (X = moisture, dry basis):

   $$X = \frac{X_m C K a_w}{(1-K a_w)(1-K a_w + C K a_w)}$$

   - GAB: Blahovec & Yanniotis (2010), Czech J. Food Sci. 28(5):345-354. GAB fits poorly at high $a_w$.
   - Coal, ore and limestone with free surface water sit at $a_w \approx 1$, so method 1 only resolves the low (hygroscopic) moisture range; above that it saturates.
   - A fully wet surface approaches wet-bulb only when radiation and conduction are small. Sun and low wind push it above wet-bulb, so $T_s$ alone is not enough.

2. Normalized index (most practical). W runs from 0 (dry) to 1 (wet) and cancels most weather effects. $T_{wb}$ from air temperature and humidity (Stull 2011); $T_{dry}$ from a dry reference. Fit moisture = f(W) with 20-50 lab samples.

   $$W = \frac{T_{dry} - T_s}{T_{dry} - T_{wb}}$$

   - $T_{dry}$ is the surface temperature of the same material when dry, under the same weather (e.g. a dry reference tray in view), not air temperature plus an offset.
   - Same idea as the Crop Water Stress Index (Idso et al. 1981; Jackson et al. 1981) but inverted: CWSI is 1 when dry, W is 1 when wet.
   - Stull (2011) wet-bulb formula (T in °C, RH in %):

   $$T_{wb} = T\,\arctan\!\left[0.151977\,(RH+8.313659)^{1/2}\right] + \arctan(T+RH) - \arctan(RH-1.676331) + 0.00391838\,RH^{3/2}\arctan(0.023101\,RH) - 4.686035$$

   - Valid for RH 5-99% and T -20 to 50 °C (not for cold and dry together). Error -1 to +0.65 °C, MAE < 0.3 °C. Check value: 20 °C, 50% RH gives 13.7 °C.
   - Assumes sea-level pressure (1013.25 hPa): needs correction for high-altitude mines.

3. Thermal inertia. Wet material heats and cools more slowly. Heat briefly (IR lamp or sun), measure the cooling rate over frames. Sees slightly below the surface.

   $$P = \sqrt{k \rho c}, \quad c = \frac{c_{solid} + X c_{water}}{1 + X}$$

   - X = kg water / kg dry solid; c is specific heat per kg of moist mass. $c_{water}$ = 4.18 kJ/kgK.
   - Use moist bulk density for $\rho$ (same basis as c). Water raises both c and k.

Limits:

- Hot process material breaks methods 1-2.
- Emissivity: water in 8-14 µm is 0.95-0.98 in common tables (0.98 best supported at near-normal view; falls at grazing angles). Limestone 0.96-0.98 (vendor tables). Coal and iron ore: no sourced value found; measure on site (e.g. contact thermocouple or emissivity tape reference). Wetting shifts a porous surface's emissivity toward water's, so emissivity error is coupled to moisture.
- All three methods measure surface, not bulk, moisture. LWIR emission comes from the top micrometres: a dry crust over wet material reads dry; a thin wet film over dry material reads wet.

## ML models and tools

Start with gradient boosting on physics features; move to a CNN or DINOv2 past about 1,000 labeled pairs. All open source (see licence notes).

| Job | Options | License |
|---|---|---|
| Baseline regression | XGBoost, LightGBM on temperature stats + W, T_wb, ambient | XGBoost Apache-2.0, LightGBM MIT |
| Deep regression | ResNet, EfficientNet, ConvNeXt (timm) | timm Apache-2.0 (EfficientNet not checked in this pass; ResNet, ConvNeXt confirmed) |
| Small data | DINOv2 frozen features + regression head | Apache-2.0 (code + weights; some derived models e.g. XRay-DINO are non-commercial) |
| Material segmentation | SAM 2, U-Net | SAM 2 Apache-2.0 |
| Clumping, blockages | Anomalib (PatchCore, PaDiM) | Apache-2.0 (PatchCore, PaDiM included) |
| Foreign objects, lumps | YOLO (Ultralytics), RT-DETR | Ultralytics AGPL-3.0 (enterprise license sold); original RT-DETR (lyuwenyu/RT-DETR) Apache-2.0 |
| Smoothing over time | Kalman filter, rolling median, LSTM | n/a |
| Edge deployment | ONNX to TensorRT on NVIDIA Jetson | trtexec builds an engine from ONNX; build the engine on the target JetPack version |
| Reading temperatures | FLIR Atlas SDK, Optris SDKs (see below), flirpy, flirimageextractor | flirpy MIT, flirimageextractor MIT |
| SCADA/DCS link | pymodbus (Modbus), asyncua (OPC-UA) | pymodbus BSD-3-Clause, asyncua LGPL-3.0 |

- "Optris PIX Connect SDK" does not exist under that name. Real options: Connect SDK (Windows only, PIX Connect must run in background), Direct SDK (no PIX Connect, Linux usable), and the newer Optris Thermal Camera SDK "otcsdk".
- FLIR Atlas SDK exists; the MATLAB edition is discontinued; check current language editions (unverified).
- flirpy supports Lepton via PureThermal (capture + telemetry), Boson, Tau 2.
- No pretrained "IR image to temperature" model is needed: radiometric cameras output calibrated per-pixel temperatures. Train on those, not on colored video.

## Hardware and prices

Prototype with a Lepton 3.5 or Optris Xi 80; pilot with the Optris Xi 400 CM. US list prices (vendor pages in Sources, checked 2026-11-14); India adds import duty and GST.

| Camera | Resolution | Price (USD) | Notes |
|---|---|---|---|
| FLIR Lepton 3.5 + PureThermal Mini Pro JST-SR (SparkFun DEV-17544) | 160×120 | 369.95 | Radiometric. ±5 °C or 5% (typical, high gain); ±10 °C or 10% low gain; about 9 Hz (unverified). "GroupGets does not ship to India" is unverified; Lepton is export-controlled (ECCN 6A993.a), so check before ordering |
| Optris Xi 80 | 80×80 | 1,200 (all lenses) | Entry industrial; -20 to 900 °C. Accuracy and frame rate not verified |
| Optris Xi 400 | 382×288 | 2,995 (3,095 macro lens) | 80 Hz; ranges -20-100 / 0-250 / 150-900 °C; accuracy ±2 °C or ±2% stated only from 150 °C |
| Optris Xi 400 CM | 382×288 | 4,825 | Outdoor housing (heater and fan, -40 to 50 °C ambient per search, unverified) + 1280×720 visible camera. Not the same as Xi 410 (3,675-3,750) |
| FLIR A50 R&D kit | 464×348 | 7,600 (51° lens) / 7,740 (29°, 95°) | GigE/PoE; about 30 Hz (snippet); ±2 °C or ±2% |
| FLIR A70 R&D kit | 640×480 (+1280×960 visible) | 9,800-9,960 (9,960 for 29° lens; 9,800 for 51°, 95°) | GigE/PoE, RTSP/GigE Vision; ±2 °C or ±2% |
| Optris PI 640i | 640×480 | 10,910 (T150 1500 °C-range SKU; 10,625 microscope optics) | 32 Hz (125 Hz subframe); 900 °C standard, 1500 °C optional (200-1500 °C) |

Also budget for a dust housing with air purge, mounting, cabling, an ambient temperature/humidity sensor, and an edge PC (about $500-2,000, planning estimate).

India sourcing (all unverified, names from search):

- Optris: MANGLAM, Servilink Systems (Vadodara).
- Teledyne FLIR: FLIR Systems India (Delhi, subsidiary), Atos Instruments, Vamara Techware (Chennai).
- GST likely 18% (HSN 8525/9025/9027 depending on classification). Basic customs duty unverified: confirm with a customs broker.

## Build steps

1. Define spec: material, moisture range, target accuracy (e.g. ±0.5-1% absolute).
2. Buy a radiometric camera, housing with air purge, ambient sensor.
3. Collect lab and plant data with time-synced oven-dry ground truth.
4. Preprocess: per-pixel temperatures, crop to material, compute W, T_wb, T_air - T_s, cooling rate.
5. Train gradient-boosting baseline, then CNN or DINOv2.
6. Validate split by day or batch, never by random frame.
7. Deploy on edge; send readings to SCADA/DCS via OPC-UA or Modbus; add alarm thresholds.
8. Check weekly against lab samples; retrain on drift.

## Risks

- Surface only: bulk moisture can differ (see Limits).
- Confounders: sun, process heat (clinker, sinter), ambient, wind, layer depth, particle size, emissivity. Feed them to the model.
- Signal saturation at high moisture (surface approaches wet-bulb, and $a_w \approx 1$).
- Per-material calibration required; coal and limestone differ.
- Lab noise caps accuracy: model cannot beat ground-truth error.
- Data leakage: adjacent frames are near-identical; split by time.
- Colored video loses accuracy: temperatures recovered from colour-palette (non-radiometric) video are relative, not absolute; error depends on palette, auto-scaling (AGC can rescale every frame) and compression. Not quantified here; use a radiometric stream.
- Alternative or reference sensors (specs not checked):
  - Microwave: Berthold online moisture measurement.
  - NIR: KPM Analytics NIR-7000, Envea M-Sens NIR.

## Next actions

- [ ] Fix target material, moisture range and accuracy spec
- [ ] Request Indian distributor quotes (Optris, Teledyne FLIR)
- [ ] Buy prototype camera and build lab rig
- [ ] Collect first 50 lab samples; fit W-index calibration curve
- [ ] Plan plant pilot with sampling protocol

## Practical notes

- Camera accuracy vs W: absolute accuracy is ±2 °C (±5 °C for Lepton), comparable to the whole $T_{dry} - T_{wb}$ span on humid days. Compute W from temperature differences within the same image (material vs a dry reference tray, and a wetted reference), not from absolute readings; this cancels most camera offset. Accuracy specs above are from 150 °C, so check near-ambient accuracy with a reference target.

## Sources

- Ripik: https://www.ripik.ai/material-moisture-analysis
- IEEE DataPort Iron Ore Powder Dataset: https://ieee-dataport.org/node/14778 (DOI 10.21227/5gcj-hx24)
- Choudhary et al. (2020), coal: https://www.jmma.tfbor.bg.ac.rs/Volumes/2020/jmma_4_20.pdf
- Zhou & Liu (2023), green pellets: https://doi.org/10.1007/s42243-023-00968-8
- Gorai et al. (2021), coal: https://link.springer.com/content/pdf/10.1007/s40789-020-00370-9.pdf
- Standards: ISO 589 https://www.iso.org/standard/45370.html ; ISO 3087 https://www.iso.org/standard/72159.html ; IS 1350-1 https://shop.standards.ie/en-ie/standards/is-1350-part-1-2025-190294_saig_bis_bis_3641081
- NIR/microwave: https://kpmanalytics.com/products/moisture-compositional/nir-7000-online-moisture-sensor , https://envea.global/s/process/moisture/m-sens-nir , https://berthold.com/en-us/process-control/products/online-moisture-measurement
- GAB (Blahovec & Yanniotis 2010): https://doi.org/10.17221/146/2009-CJFS
- Stull (2011), DOI 10.1175/JAMC-D-11-0143.1; implementation: https://www.ncl.ucar.edu/Document/Functions/Contributed/wetbulb_stull.shtml
- Wet-bulb: https://en.wikipedia.org/wiki/Wet-bulb_temperature
- Emissivity tables: https://www.thermoworks.com/blogs/thermoblog/emissivity
- Surface-only IR: https://www.infratec.eu/thermography/wegweiser/physical-principles
- Lepton: https://www.sparkfun.com/purethermal-mini-pro-jst-sr-with-flir-lepton-3-5.html ; export control: https://groupgets.com/pages/exportcontrol
- Optris Xi prices: https://www.globaltestsupply.com/online/optris-xi-series/sort:ProductProperties.inventory/direction:desc ; Xi 400 datasheet: https://movitherm.com/wp-content/uploads/2024/02/Optris-Xi-400-Datasheet-MoviTHERM-Official-Distributor.pdf ; Xi 400 CM: https://www.globaltestsupply.com/category/thermal-imagers/page:4/sort:name/direction:desc
- FLIR A50/A70: https://www.globaltestsupply.com/online/flir-a50a70-series-thermal-core-cameras ; A70 29 kit: https://www.globaltestsupply.com/product/flir-a70-research-and-development-kit-with-29-degree-spatial-resolution
- Optris PI 640i: https://www.globaltestsupply.com/category/optris-thermal-imagers ; datasheet: https://www.ibt.co.il/wp-content/uploads/2022/04/PI_640i-DS-EN2021-06-A-1.pdf
- Optris SDKs: https://optris.com/en-us/products/infrared-cameras/software-pix-connect , https://optris.com/en/support/downloads/software , https://optris.github.io/otcsdk_downloads/basic-usage.html
- FLIR Atlas SDK for MATLAB (discontinued): https://www.flir.com/products/flir-atlas-sdk-for-matlab/
- TensorRT: https://docs.nvidia.com/deeplearning/tensorrt/latest/installing-tensorrt/installing.html
- Licenses (prefix https://): github.com/dmlc/xgboost, github.com/lightgbm-org/LightGBM, pypi.org/project/timm, github.com/facebookresearch/dinov2, github.com/facebookresearch/sam2, github.com/open-edge-platform/anomalib, github.com/ultralytics/ultralytics, github.com/lyuwenyu/RT-DETR, github.com/LJMUAstroecology/flirpy, pypi.org/project/flirimageextractor, pypi.org/project/asyncua, pypi.org/project/pymodbus
