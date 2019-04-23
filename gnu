module swap PrgEnv-intel PrgEnv-gnu
module add gcc/7.3.0
module add cray-netcdf/4.6.1.2
module add cray-mpich/7.7.2

export NETCDF=/opt/cray/pe/netcdf/4.6.1.2/GNU/7.1
export NETCDFPATH=/opt/cray/pe/netcdf/4.6.1.2/GNU/7.1
export WRFIO_NCD_LARGE_FILE_SUPPORT=0
export WRF_DA_CORE=0
export JASPERLIB=/projects/climate_severe/WRF/Libs/lib
export JASPERINC=/projects/climate_severe/WRF/Libs/include
export LD_LIBRARY_PATH=/projects/climate_severe/WRF/Libs:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/opt/cray/pe/gcc-libs/:$LD_LIBRARY_PATH
export LIBINCLUDE="/projects/climate_severe/WRF/Libs:/projects/climate_severe/WRF/Libs/include":$LIBINCLUDE

export PATH=$PATH:/projects/climate_severe/WRF/grib2/wgrib2/
