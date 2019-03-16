import arcpy
import parameters
import my_utils
#import utils

# import decimal
start = time.time()
arcpy.CheckOutExtension('Spatial')
arcpy.env.overwriteOutput = 1

# nastaveni pracovni databaze
work_dtb = parameters.work_dtb
arcpy.env.workspace = '.\\{}.gdb'.format(work_dtb)
workspace = arcpy.env.workspace

# inputs
final_line = parameters.cl_output

# output
cl_polygon = parameters.cl_polygon

# vypocet
arcpy.Buffer_analysis (final_line, cl_polygon, 'cl_size', 'LEFT', 'FLAT', '', '', 'PLANAR')


end = time.time()
print 'time', end-start