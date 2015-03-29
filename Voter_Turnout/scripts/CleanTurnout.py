import sys, os
import csv
from string import *

if len( sys.argv ) != 2 or sys.argv[ 1 ] in ['-h', '--help', '-help', '/h', '/?']:
	print '\nDescription: detects potential data integrity issues in raw turnout file\nand generates flattened version of file with ward and devision as separate columns'
	print '\nOutput: a file with the same name plus "_Flat" added to the end'
	print '\nUsage:\n\tpython {0} [path to base turnout file]'.format( sys.argv[ 0 ] )
	print '\nExample:\n\tpython {0} ../2014_General_Election_Voter_Turnout.csv'.format( sys.argv[ 0 ] )
	print '\t(generates ../2014_General_Election_Voter_Turnout_Flat.csv)'
	print ''
	sys.exit( 0 )

def IsNoneOrEmpty( s ):
	return s is None or len( s.strip() ) == 0
	
def ParseWardAndDivision( precinct ):
	return ( int( precinct[ :-2 ] ), int( precinct[ -2: ] ) )

filePath = sys.argv[ 1 ]
( filePathWithoutExtension, fileExtension ) = os.path.splitext( filePath )
( filePathBase, fileNameWithoutExtension ) = os.path.split( filePathWithoutExtension, )
outFilePath = os.path.join( filePathBase, fileNameWithoutExtension + '_Flat' + fileExtension )

print 'Reading from {0}, writing to {1}...'.format( filePath, outFilePath )

issues = []
skippedData = []

with open( filePath, 'r' ) as inFile:
	with open( outFilePath, 'w' ) as outFile:
		reader = csv.reader( inFile )
		reader.next()
		writer = csv.writer( outFile, lineterminator='\n' )
		writer.writerow( [ 'Ward', 'Division', 'Political Party', 'Count of Voters by Party' ] )

		lastWard = None
		lastDivision = None
		lastPrecinct = None
		lastGoodWard = None
		lastGoodDivision = None
		lastRowWasTotal = True
		
		for row in reader:
			expectingPrecinct = lastRowWasTotal
			lastRowWasTotal = False
			empties = map( lambda c: IsNoneOrEmpty( c ), row )
			
			if all( empties ):
				issues.append( 'Blank row {0}: {1}'.format( reader.line_num, ','.join( row ) ) )
				continue
				
			if not empties[ 1 ] and ( row[ 1 ].startswith( 'Count of Voters' ) or row[ 1 ].startswith( 'Total Voters on Report' ) ):
				if row[ 1 ].startswith( 'Count' ) and not row[ 1 ].find( 'election' ):
					try:
						words = row[ 1 ].split( ' ' )
						precinct = words[-1][:-1]
						( ward, division ) = ParseWardAndDivision( precinct )
						if lastGoodWard is not None and lastGoodDivision is not None and ( ward != lastGoodWard or division != lastGoodDivision ):
							issues.append( 'Totals row precinct does not match last good precinct, prior rows may have been incorrectly flattened - row {0}: {1}'.format( reader.line_num, ','.join( row ) ) )

						# TODO: sum counts and validate total?
					except:
						issues.append( 'Invalid precinct in totals row {0}: {1}'.format( reader.line_num, ','.join( row ) ) )

				lastRowWasTotal = True
				lastWard = None
				lastDivision = None

				print 'Skipping totals row {0}: {1}'.format( reader.line_num, ','.join( row ) )
				continue

			if not empties[ 0 ]:
				precinct = row[ 0 ]
				try:
					( ward, division ) = ParseWardAndDivision( precinct )

					if not expectingPrecinct:
						print 'Unexpected precinct (likely pagination) on row {0}: {1}'.format( reader.line_num, ','.join( row ) )
					if lastGoodWard is not None and lastGoodDivision is not None:
						if ward < lastGoodWard or (ward == lastGoodWard and division < lastGoodDivision ):
							raise Exception( 'Precincts should increase monotonically' )
						if ward > lastGoodWard and division != 1:
							raise Exception( 'New ward did not start with division #1' )

					lastWard = ward
					lastDivision = division
					lastGoodWard = lastWard
					lastGoodDivision = lastDivision
					lastPrecinct = precinct
				except Exception as e:
					issues.append( 'Invalid precinct? ({0}) on row {1}: {2}'.format( e, reader.line_num, precinct ) )
					lastWard = None
					lastDivision = None
					
				if empties[ 1 ] and empties[ 2 ]:
					continue

			if lastWard is None or lastDivision is None:
				skippedData.append( 'Skipping data with invalid precinct on row {0}: {1}'.format( reader.line_num, ','.join( row ) ) )
				continue
				
			if empties[ 1 ]:
				issues.append( 'No party on row {0}: {1}'.format( reader.line_num, ','.join( row ) ) )
				continue;

			if empties[ 2 ]:
				issues.append( 'No count on row {0}, precinct {1}: {2}'.format( reader.line_num, lastPrecinct, row[ 1 ] ) )
				continue

			try:
				int( row[2] )
			except:
				issues.append( 'Count is not a number on row {0}, precinct {1}: {2}'.format( reader.line_num, lastPrecinct, ','.join( row ) ) )
			
			writer.writerow( [ lastWard, lastDivision, row[ 1 ], row[ 2 ] ] )

print ''
print 'Done'

if len( issues ) > 0:
	print ''
	print '{0} issues found:'.format( len( issues ) )
	print '\n'.join( issues )
	print ''
	print 'End of issues'
	
if len( skippedData ) > 0:
	print ''
	print 'Could not determine precinct on {0} rows (these were not written to the _Flat file):'.format( len( skippedData ) )
	print '\n'.join( skippedData )
	print ''
	print 'End of skipped rows'

if len( issues ) + len( skippedData ) == 0:
	print 'Clean!'