if [ ! -d 'samples' ]; then
  mkdir 'samples'
fi

R -f --no-restore --slave --no-save generate_samples.r

python ../../simulate.py samples/*.dat single_run --max_sample=50

R -f --no-restore --slave --no-save visualize_simulation.r
