if [ ! -d 'samples' ]; then
  mkdir 'samples'
fi

echo "WARNING: This may take upward of 40 minutes to complete all the simulations at 1000 repetitions"

R -f --no-restore --slave --no-save generate_samples.r

python ../../simulate.py samples/*.dat calibration --max_sample=30 --calibrate 20

R -f --no-restore --slave --no-save calibrate_tests.r
