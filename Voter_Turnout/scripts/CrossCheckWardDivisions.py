import sys, os
import csv
from string import *

if len( sys.argv ) < 2 or sys.argv[ 1 ] in ['-h', '--help', '-help', '/h', '/?']:
	print '\nDescription: verfies ward and devisions continuity in each source file\nand cross-checks the set of wards and devisions across all sources.'
	print 'Each source file must be CSV with a header row and must have both a Ward and Division column.'
	print '\nUsage:\n\tpython {0} [path to source file, ...]'.format( sys.argv[ 0 ] )
	print '\nExample:\n\tpython {0} ../2014_General_Election_Voter_Turnout.csv ../../Voter_Registry/QualifiedVoterListing.csv'.format( sys.argv[ 0 ] )
	print ''
	sys.exit( 0 )

class WardSource:
	def __init__( self, path ):
		self.Path = path
		self.WardDivisions = {}
		
	def AddWardDivision( self, ward, division ):
		divisions = self.WardDivisions.get( ward )
		if divisions is None:
			divisions = set()
			self.WardDivisions[ ward ] = divisions
		divisions.add( division )

class WardValidator:
	def __init__( self ):
		self.Reset()
	
	def Reset( self ):
		self.Issues = []
		
	def Validate( self, wardSource ):
		self.ValidateContinuity( wardSource.WardDivisions.keys(), 'ward' )
			
		for (ward, divisions) in wardSource.WardDivisions.items():
			self.ValidateContinuity( divisions, 'ward {0} division'.format( ward ) )

	def ValidateContinuity( self, numbers, numberName ):
		prevNumber = None
		for number in sorted( numbers ):
			if prevNumber is not None and number != prevNumber + 1:
				self.Issues.append( '{0} {1} does not directly follow {0} {2}'.format( numberName, number, prevNumber ) )
			prevNumber = number
			
class WardCrossChecker:
	def __init__( self, wardSources ):
		self.WardSources = wardSources
		self.Issues = []
		
	def Check( self ):
		for i in range( 1, len( wardSources ) ):
			for j in range( i ):
				self.CheckPair( wardSources[ i ], wardSources[ j ] )
				
	def CheckPair( self, left, right ):
		for diff in set( left.WardDivisions.keys() ).difference( set( right.WardDivisions.keys() ) ):
			self.Issues.append( 'ward {0} is in {1} but not {2}'.format( diff, left.Path, right.Path ) )
			
		for diff in set( right.WardDivisions.keys() ).difference( set( left.WardDivisions.keys() ) ):
			self.Issues.append( 'ward {0} is in {1} but not {2}'.format( diff, right.Path, left.Path ) )

		if len( left.WardDivisions ) < len( right.WardDivisions ):
			tmp = left
			left = right
			right = tmp
	
		for ( ward, leftDivisions ) in left.WardDivisions.items():
			rightDivisions = right.WardDivisions.get( ward )
			if rightDivisions is None:
				continue
			
			for diff in leftDivisions.difference( rightDivisions ):
				self.Issues.append( 'in ward {0}, {1} has division {2}, but {3} does not'.format( ward, left.Path, diff, right.Path ) )

			for diff in rightDivisions.difference( leftDivisions ):
				self.Issues.append( 'in ward {0}, {1} has division {2}, but {3} does not'.format( ward, right.Path, diff, left.Path ) )
		
wardSources = []
for path in sys.argv[1:]:
	wardSource = WardSource( path )
	print ''
	print 'Loading Wards and Divisions from {0}...'.format( path )
	with open( path, 'r' ) as inFile:
		reader = csv.reader( inFile )
		header = reader.next()
		fieldNames = map( lambda n: n.lower(), header )
		wardIndex = fieldNames.index( 'ward' )
		if wardIndex < 0:
			raise Exception( 'Could not find column for "ward"' )
		divisionIndex = fieldNames.index( 'division' )
		if divisionIndex < 0:
			raise Exception( 'Could not find column for "division"' )
			
		for row in reader:
			ward = int( row[ wardIndex ] )
			division = int( row[ divisionIndex ] )
			
			wardSource.AddWardDivision( ward, division )
	wardSources.append( wardSource )
	print '... load complete: {0} wards loaded with {1} total divisions'.format( len( wardSource.WardDivisions ), sum( map( lambda d: len( d ), wardSource.WardDivisions.values() ) ) )
	
print ''
print 'All sources loaded.'
print ''

validator = WardValidator()

for wardSource in wardSources:
	validator.Reset()
	print 'Validating {0}...'.format( wardSource.Path )
	validator.Validate( wardSource )
	print '\n'.join( validator.Issues )
	print 'Validation complete: {0} issues'.format( len( validator.Issues ) )
	print ''

print 'All validation complete'

print ''
print 'Cross checking wards & divisions...'

crossChecker = WardCrossChecker( wardSources )
crossChecker.Check()

print '\n'.join( crossChecker.Issues )
print 'All cross checking complete.'
print ''
