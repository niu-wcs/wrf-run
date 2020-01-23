#!/usr/bin/python
# Scheduler.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains methods to generate different job-scripts based on the scheduling system

from datetime import timedelta

# Scheduler_Settings: Class responsible for storing the information about different schedulers
class Scheduler_Settings:
	stored_table = {}
	scheduler = ""
	
	def __init__(self, scheduler):
		self.scheduler = scheduler
		self.stored_table = {
			"COBALT": {
				"header-type": "#!/bin/bash",
				"header-tag": "#COBALT",
				"header-jobname": None,
				"header-account": "-A",
				"header-nodes": "-n",
				"header-tasks": None,
				"header-jobtime": "-t",
				"header-jobqueue": "-q",
				"extra-exports": "export n_nodes=$COBALT_JOBSIZE\n" +
				                 "export n_mpi_ranks_per_node=[ranks_per_node]\n" +
								 "export n_mpi_ranks=$(($n_nodes * $n_mpi_ranks_per_node))\n" +
								 "export n_openmp_threads_per_rank=[omp_threads_per_rank]\n" +
								 "export n_hardware_threads_per_core=[threads_per_core]\n" +
								 "export n_hardware_threads_skipped_between_ranks=[threads_skipped_per_rank]",
				"cmdline": "--mode script",
				"time-format": "minutes",
				"subcmd": "qsub",
				"runcmd": "aprun",
				"subargs": "-n $n_mpi_ranks -N $n_mpi_ranks_per_node \\\n" +
						   "--env OMP_NUM_THREADS=$n_openmp_threads_per_rank --cc depth \\\n" +
						   "-d $n_hardware_threads_skipped_between_ranks \\\n" +
						   "-j $n_hardware_threads_per_core",
			},
			
			"PBS": {
				"header-type": "#!/bin/bash",
				"header-tag": "#PBS",
				"header-jobname": "-N",
				"header-account": "-A",
				"header-nodes": "-l nodes",
				"header-tasks": "-l ppn",
				"header-jobtime": "-l walltime",
				"header-jobqueue": None,
				"extra-exports": None,
				"cmdline": "",
				"time-format": "timestring",
				"subcmd": "qsub",				
				"runcmd": "mpirun",
				"subargs": "-n [total_processors]",
			},

			"SLURM": {
				"header-type": "#!/bin/bash",
				"header-tag": "#SBATCH",
				"header-jobname": "--job-name",
				"header-account": "--account",
				"header-nodes": "--nodes",
				"header-tasks": "--ntasks-per-node",
				"header-jobtime": "--time",
				"header-jobqueue": None,
				"extra-exports": None,
				"cmdline": "",
				"time-format": "timestring",
				"subcmd": "sbatch",
				"runcmd": "srun",
				"subargs": "-n [total_processors]"
			},	

		}
		
	def validScheduler(self):
		return self.scheduler in self.stored_table
	
	def fetch(self):
		return self.stored_table[self.scheduler]
		
	def convert_to_timestring(self, min):
		if (self.fetch()["time-format"] == "timestring"):
			delta = timedelta(minutes = int(min))
			outTime = '%02d:%02d:%02d' % (delta.days*24 + delta.seconds // 3600, (delta.seconds % 3600) // 60, delta.seconds % 60)
			return outTime
		elif (self.fetch()["time-format"] == "minutes"):
			return min
		else:
			return None