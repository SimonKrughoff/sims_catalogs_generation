import sqlite3
from numpy.random import random, seed
import numpy, json

from lsst.sims.catalogs.generation.db import CatalogDBObject

__all__ = ["getOneChunk", "writeResult", "sampleSphere", "myTestGals",
           "makeGalTestDB", "myTestStars", "makeStarTestDB", "makePhoSimTestDB"]

def getOneChunk(results):
    try:
        chunk = results.next()
    except StopIteration:
        raise RuntimeError("No results were returned.  Cannot run tests.  Try increasing the size of the"+
                           " test database")
    return chunk

def writeResult(result, fname):
    fh = open(fname, 'w')
    first = True
    for chunk in result:
        if first:
            fh.write(",".join([str(el) for el in chunk.dtype.names])+"\n")
            first = False
        for i in xrange(len(chunk)):
            fh.write(",".join([str(chunk[name][i]) for name in chunk.dtype.names])+"\n")
    fh.close()

def sampleSphere(size, ramin = 0., dra = 2.*numpy.pi):
    #From Shao 1996: "Spherical Sampling by Archimedes' Theorem"
    ra = random(size)*dra
    ra += ramin
    ra %= 2*numpy.pi
    z = random(size)*2. - 1.
    dec = numpy.arccos(z) - numpy.pi/2.
    return ra, dec


class myTestGals(CatalogDBObject):
    objid = 'testgals'
    tableid = 'galaxies'
    idColKey = 'id'
    #Make this implausibly large?
    appendint = 1022
    dbAddress = 'sqlite:///testDatabase.db'
    raColName = 'ra'
    decColName = 'decl'
    spatialModel = 'SERSIC2D'
    columns = [('id', None, int),
               ('raJ2000', 'ra*%f'%(numpy.pi/180.)),
               ('decJ2000', 'decl*%f'%(numpy.pi/180.)),
               ('umag', None),
               ('gmag', None),
               ('rmag', None),
               ('imag', None),
               ('zmag', None),
               ('ymag', None),
               ('magNormAgn', 'mag_norm_agn', None),
               ('magNormDisk', 'mag_norm_disk', None),
               ('magNormBulge', 'mag_norm_bulge', None),
               ('redshift', None),
               ('a_disk', None),
               ('b_disk', None),
               ('a_bulge', None),
               ('b_bulge', None),]

def makeGalTestDB(filename='testDatabase.db', size=1000, seedVal=None, **kwargs):
    """
    Make a test database to serve information to the myTestGals object
    @param size: Number of rows in the database
    @param seedVal: Random seed to use
    """
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE galaxies
                     (id int, ra real, decl real, umag real, gmag real, rmag real,
                     imag real, zmag real, ymag real,
                     mag_norm_agn real, mag_norm_bulge real, mag_norm_disk real,
                     redshift real, a_disk real, b_disk real, a_bulge real, b_bulge real, varParamStr text)''')
        conn.commit()
    except:
        raise RuntimeError("Error creating database.")
    if seedVal:
        seed(seedVal)
    ra, dec = sampleSphere(size, **kwargs)
    #Typical colors for main sequece stars
    umg = 1.5
    gmr = 0.65
    rmi = 1.0
    imz = 0.45
    zmy = 0.3
    mag_norm_disk = random(size)*6. + 18.
    mag_norm_bulge = random(size)*6. + 18.
    mag_norm_agn = random(size)*6. + 19.
    redshift = random(size)*2.5

    a_disk = random(size)*2.
    flatness = random(size)*0.8 # To prevent linear galaxies
    b_disk = a_disk*(1 - flatness)

    a_bulge = random(size)*1.5
    flatness = random(size)*0.5
    b_bulge = a_bulge*(1 - flatness)

    #assume mag norm is g-band (which is close to true)
    mag_norm = -2.5*numpy.log10(numpy.power(10, mag_norm_disk/-2.5) + numpy.power(10, mag_norm_bulge/-2.5) +
                                numpy.power(10, mag_norm_agn/-2.5))
    umag = mag_norm + umg
    gmag = mag_norm
    rmag = gmag - gmr
    imag = rmag - rmi
    zmag = imag - imz
    ymag = zmag - zmy
    for i in xrange(size):
        period = random()*490. + 10.
        amp = random()*5. + 0.2
        varParam = {'varMethodName':'testVar', 'pars':{'period':period, 'amplitude':amp}}
        paramStr = json.dumps(varParam)
        qstr = '''INSERT INTO galaxies VALUES (%i, %f, %f, %f,
                     %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f,
                     %f, %f, '%s')'''%\
                   (i, numpy.degrees(ra[i]), numpy.degrees(dec[i]), umag[i], gmag[i], rmag[i], imag[i],
                   zmag[i], ymag[i], mag_norm_agn[i], mag_norm_bulge[i], mag_norm_disk[i], redshift[i],
                   a_disk[i], b_disk[i], a_bulge[i], b_bulge[i], paramStr)
        c.execute(qstr)
    c.execute('''CREATE INDEX gal_ra_idx ON galaxies (ra)''')
    c.execute('''CREATE INDEX gal_dec_idx ON galaxies (decl)''')
    conn.commit()
    conn.close()

class myTestStars(CatalogDBObject):
    objid = 'teststars'
    tableid = 'stars'
    idColKey = 'id'
    #Make this implausibly large?
    appendint = 1023
    dbAddress = 'sqlite:///testDatabase.db'
    raColName = 'ra'
    decColName = 'decl'
    columns = [('id', None, int),
               ('raJ2000', 'ra*%f'%(numpy.pi/180.)),
               ('decJ2000', 'decl*%f'%(numpy.pi/180.)),
               ('umag', None),
               ('gmag', None),
               ('rmag', None),
               ('imag', None),
               ('zmag', None),
               ('ymag', None),
               ('magNorm', 'mag_norm', float)]

def makeStarTestDB(filename='testDatabase.db', size=1000, seedVal=None, **kwargs):
    """
    Make a test database to serve information to the myTestStars object
    @param size: Number of rows in the database
    @param seedVal: Random seed to use
    """
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE stars
                     (id int, ra real, decl real, umag real, gmag real, rmag real,
                     imag real, zmag real, ymag real, mag_norm real,
                     radialVelocity real, properMotionDec real, properMotionRa real, varParamStr text)''')
        conn.commit()
    except:
        raise RuntimeError("Error creating database.")
    if seedVal:
        seed(seedVal)
    ra, dec = sampleSphere(size, **kwargs)
    #Typical colors
    umg = 1.5
    gmr = 0.65
    rmi = 1.0
    imz = 0.45
    zmy = 0.3
    mag_norm = random(size)*6. + 18.
    #assume mag norm is g-band (which is close to true)
    umag = mag_norm + umg
    gmag = mag_norm
    rmag = gmag - gmr
    imag = rmag - rmi
    zmag = imag - imz
    ymag = zmag - zmy
    radVel = random(size)*50. - 25.
    pmRa = random(size)*4./(1000*3600.) # deg/yr
    pmDec = random(size)*4./(1000*3600.) # deg/yr
    for i in xrange(size):
        period = random()*490. + 10.
        amp = random()*5. + 0.2
        varParam = {'varMethodName':'testVar', 'pars':{'period':period, 'amplitude':amp}}
        paramStr = json.dumps(varParam)
        qstr = '''INSERT INTO stars VALUES (%i, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, '%s')'''%\
                  (i, numpy.degrees(ra[i]), numpy.degrees(dec[i]), umag[i], gmag[i], rmag[i],
                   imag[i], zmag[i], ymag[i], mag_norm[i], radVel[i], pmRa[i], pmDec[i], paramStr)
        c.execute(qstr)
    c.execute('''CREATE INDEX star_ra_idx ON stars (ra)''')
    c.execute('''CREATE INDEX star_dec_idx ON stars (decl)''')
    conn.commit()
    conn.close()

def makePhoSimTestDB(filename='PhoSimTestDatabase.db', size=1000, seedVal=32, **kwargs):
    """
    Make a test database to storing cartoon information for the test phoSim input
    catalog to use.

    The method will return an ObservationMetaData object guaranteed to encompass the
    objects in this database.
    """

    if os.path.exists(filename):
        os.unlink(filename)

    #just an example of some valid SED file names
    galaxy_seds = ['Const.80E07.02z.spec','Inst.80E07.002Z.spec','Burst.19E07.0005Z.spec']
    agn_sed = 'agn.spec'
    star_seds = ['km20_5750.fits_g40_5790','m2.0Full.dat','bergeron_6500_85.dat_6700']

    numpy.random.seed(seedVal)

    #create the ObservationMetaData object
    mjd = 52000.0
    alt = numpy.pi/2.0
    az = 0.0
    band = 'r'
    testSite = Site()
    centerRA, centerDec = altAzToRaDec(alt,az,testSite.longitude,testSite.latitude,mjd)
    rotTel = getRotTelPos(az, centerDec, testSite.latitude, 0.0)

    obsDict = calcObsDefaults(centerRA, centerDec, alt, az, rotTel, mjd, band,
                 testSite.longitude, testSite.latitude)

    obsDict['Opsim_expmjd'] = mjd
    radius = 0.1
    phoSimMetadata = OrderedDict([
                      (k, (obsDict[k],numpy.dtype(type(obsDict[k])))) for k in obsDict])

    obs_metadata = ObservationMetaData(boundType = 'circle', unrefractedRA = numpy.degrees(centerRA),
                                       unrefractedDec = numpy.degrees(centerDec), boundLength = 2.0*radius,
                                       phoSimMetadata=phoSimMetadata, site=testSite)

    #Now begin building the database.
    #First create the tables.
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE galaxy_bulge
                 (galtileid int, galid int, bra real, bdec real, ra real, dec real, magnorm_bulge real,
                 sedname_bulge text, a_b real, b_b real, pa_bulge real, bulge_n int,
                 ext_model_b text, av_b real, rv_b real, u_ab real, g_ab real, r_ab real, i_ab real,
                 z_ab real, y_ab real, redshift real)''')
        conn.commit()
    except:
        raise RuntimeError("Error creating galaxy_bulge table.")

    try:
        c.execute('''CREATE TABLE galaxy
                  (galtileid int, galid int, dra real, ddec real, ra real, dec real,
                  magnorm_disk real, sedname_disk text, a_d real, b_d real, pa_disk real,
                  disk_n int, ext_model_d text, av_d real, rv_d real, u_ab real,
                  g_ab real, r_ab real, i_ab real, z_ab real, y_ab real, redshift real)''')
        conn.commit()
    except:
        raise RuntimeError("Error creating galaxy table.")

    try:
        c.execute('''CREATE TABLE galaxy_agn
                  (galtileid int, galid int, agnra real, agndec real, ra real, dec real,
                  magnorm_agn real, sedname_agn text, varParamStr text, u_ab real,
                  g_ab real, r_ab real, i_ab real, z_ab real, y_ab real, redshift real)''')
    except:
        raise RuntimeError("Error creating galaxy_agn table.")

    try:
        c.execute('''CREATE TABLE starsALL_forceseek
                  (simobjid int, ra real, decl real, gal_l real, gal_b real, magNorm real,
                  mudecl real, mura real, galacticAv real, vrad real, varParamStar text, sedFilename text, parallax real)''')
    except:
        raise RuntimeError("Error creating starsALL_forceseek table.")

    #Now generate the data to be stored in the tables.
    rr = numpy.random.sample(size)*numpy.radians(radius)
    theta = numpy.random.sample(size)*2.0*numpy.pi
    ra = numpy.degrees(centerRA + rr*numpy.cos(theta))
    dec = numpy.degrees(centerDec + rr*numpy.sin(theta))

    bra = numpy.radians(ra+numpy.random.sample(size)*0.01*radius)
    bdec = numpy.radians(dec+numpy.random.sample(size)*0.01*radius)
    dra = numpy.radians(ra + numpy.random.sample(size)*0.01*radius)
    ddec = numpy.radians(dec + numpy.random.sample(size)*0.01*radius)
    agnra = numpy.radians(ra + numpy.random.sample(size)*0.01*radius)
    agndec = numpy.radians(dec + numpy.random.sample(size)*0.01*radius)

    magnorm_bulge = numpy.random.sample(size)*4.0 + 17.0
    magnorm_disk = numpy.random.sample(size)*5.0 + 17.0
    magnorm_agn = numpy.random.sample(size)*5.0 + 17.0
    a_b = numpy.random.sample(size)*0.2
    b_b = numpy.random.sample(size)*0.2
    a_d = numpy.random.sample(size)*0.5
    b_d = numpy.random.sample(size)*0.5

    pa_bulge = numpy.random.sample(size)*360.0
    pa_disk = numpy.random.sample(size)*360.0

    av_b = numpy.random.sample(size)*0.4
    av_d = numpy.random.sample(size)*0.4
    rv_b = numpy.random.sample(size)*0.1 + 3.0
    rv_d = numpy.random.sample(size)*0.1 + 3.0

    u_ab = numpy.random.sample(size)*4.0 + 17.0
    g_ab = numpy.random.sample(size)*4.0 + 17.0
    r_ab = numpy.random.sample(size)*4.0 + 17.0
    i_ab = numpy.random.sample(size)*4.0 + 17.0
    z_ab = numpy.random.sample(size)*4.0 + 17.0
    y_ab = numpy.random.sample(size)*4.0 +17.0
    redshift = numpy.random.sample(size)*2.0

    t0_mjd = numpy.random.sample(size)*10.0+mjd
    agn_tau = numpy.random.sample(size)*1000.0 + 1000.0
    agnSeed = numpy.random.random_integers(low=2, high=4000, size=size)
    agn_sfu = numpy.random.sample(size)
    agn_sfg = numpy.random.sample(size)
    agn_sfr = numpy.random.sample(size)
    agn_sfi = numpy.random.sample(size)
    agn_sfz = numpy.random.sample(size)
    agn_sfy = numpy.random.sample(size)

    rrStar = numpy.random.sample(size)*numpy.radians(radius)
    thetaStar = numpy.random.sample(size)*2.0*numpy.pi
    raStar = centerRA + rrStar*numpy.cos(thetaStar)
    decStar = centerDec + rrStar*numpy.sin(thetaStar)
    gal_l, gal_b = AstrometryBase.equatorialToGalactic(raStar, decStar)

    raStar = numpy.degrees(raStar)
    decStar = numpy.degrees(decStar)
    gal_l = numpy.degrees(gal_l)
    gal_b = numpy.degrees(gal_b)

    magnormStar = numpy.random.sample(size)*4.0 + 17.0
    mudecl = numpy.random.sample(size)*0.0001
    mura = numpy.random.sample(size)*0.0001
    galacticAv = numpy.random.sample(size)*0.05*3.1
    vrad = numpy.random.sample(size)*1.0
    parallax = 0.00045+numpy.random.sample(size)*0.00001

    #write the data to the tables.
    for i in range(size):

        cmd = '''INSERT INTO galaxy_bulge VALUES (%i, %i, %f, %f, %f, %f, %f,
                     '%s', %f, %f, %f, %i, '%s', %f, %f, %f, %f, %f, %f, %f, %f, %f)''' %\
                     (i, i, bra[i], bdec[i], ra[i], dec[i], magnorm_bulge[i], galaxy_seds[i%len(galaxy_seds)],
                     a_b[i], b_b[i], pa_bulge[i], 4, 'CCM', av_b[i], rv_b[i], u_ab[i], g_ab[i],
                     r_ab[i], i_ab[i], z_ab[i], y_ab[i], redshift[i])
        c.execute(cmd)

        cmd = '''INSERT INTO galaxy VALUES (%i, %i, %f, %f, %f, %f, %f,
                     '%s', %f, %f, %f, %i, '%s', %f, %f, %f, %f, %f, %f, %f, %f, %f)''' %\
                     (i, i, dra[i], ddec[i], ra[i], dec[i], magnorm_disk[i],
                     galaxy_seds[i%len(galaxy_seds)], a_d[i], b_d[i], pa_disk[i], 1, 'CCM',
                     av_d[i], rv_d[i], u_ab[i], g_ab[i],
                     r_ab[i], i_ab[i], z_ab[i], y_ab[i], redshift[i])
        c.execute(cmd)

        varParam = {'varMethodName':'applyAgn',
                    'pars':{'agn_tau':agn_tau[i], 't0_mjd':t0_mjd[i],
                    'agn_sfu':agn_sfu[i], 'agn_sfg':agn_sfg[i], 'agn_sfr':agn_sfr[i],
                    'agn_sfi':agn_sfi[i], 'agn_sfz':agn_sfz[i], 'agn_sfy':agn_sfy[i],
                    'seed':int(agnSeed[i])}}

        paramStr = json.dumps(varParam)

        cmd = '''INSERT INTO galaxy_agn VALUES (%i, %i, %f, %f, %f, %f, %f, '%s', '%s',
                                               %f, %f, %f, %f, %f, %f, %f)''' %\
                                               (i, i, agnra[i], agndec[i], ra[i], dec[i],
                                               magnorm_agn[i], agn_sed, paramStr,
                                               u_ab[i], g_ab[i], r_ab[i], i_ab[i],
                                               z_ab[i], y_ab[i], redshift[i])
        c.execute(cmd)

        cmd = '''INSERT INTO starsALL_forceseek VALUES (%i, %f, %f, %f, %f, %f, %f, %f, %f, %f, %s, '%s', %f)''' %\
                  (i, raStar[i], decStar[i], gal_l[i], gal_b[i], magnormStar[i], mudecl[i], mura[i],
                  galacticAv[i], vrad[i], 'NULL', star_seds[i%len(star_seds)], parallax[i])

        c.execute(cmd)

    conn.commit()
    conn.close()
    return obs_metadata

