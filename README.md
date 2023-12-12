# Augmented Audio Reality (AAR)
Final Project - Applied Musicology for the Anthropocene (National Taiwan University, 112-1.)

## Flow Chart
![flow-chart](https://github.com/Zen-Tsai/Musicology/blob/main/flow-chart.jpg?raw=true)

## Demos
These videos are provided exclusively for educational and reporting purposes within classes at National Taiwan University. They are not intended for commercial use, distribution, or reporting outside of this specific educational context at the university. Please respect the intended use and limitations of these materials.

- https://youtu.be/FD_uPhWM8Rs
- https://youtu.be/oyUsPPuKbRs

## Installation on macOS (Tested on M1 chip)

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
(echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> /Users/user/.bash_profile
eval "$(/opt/homebrew/bin/brew shellenv)"
brew install portaudio

conda install -c conda-forge ffmpeg
conda install -c conda-forge pydub
conda install -c conda-forge pyqt
conda install -c conda-forge pyqtgraph
```

Use `python main.py` to run.
