"""
CMSSW job type plug-in
"""

import os
import tempfile

from BasicJobType import BasicJobType
from CMSSWConfig import CMSSWConfig
from UserTarball import UserTarball
from ScramEnvironment import ScramEnvironment

class CMSSW(BasicJobType):
    """
    CMSSW job type plug-in
    """


    def run(self, requestConfig):
        """
        Override run() for JobType
        """
        configArguments = {'outputFiles'            : [],
                           'InputDataset'           : [],
                           'ProcessingVersion'      : '',
                           'AnalysisConfigCacheDoc' : '', }

        # Get SCRAM environment

        scram = ScramEnvironment(logger=self.logger)

        configArguments.update({'ScramArch'    : scram.scramArch,
                                'CMSSWVersion' : scram.cmsswVersion, })

        # Build tarball
        if self.workdir:
            tarFilename   = os.path.join(self.workdir, 'default.tgz')
            cfgOutputName = os.path.join(self.workdir, 'CMSSW_cfg.py')
        else:
            _dummy, tarFilename   = tempfile.mkstemp(suffix='.tgz')
            _dummy, cfgOutputName = tempfile.mkstemp(suffix='_cfg.py')

        with UserTarball(name=tarFilename, logger=self.logger, config=self.config) as tb:
            if getattr(self.config.JobType, 'inputFiles', None) is not None:
                tb.addFiles(userFiles=self.config.JobType.inputFiles)
            uploadResults = tb.upload()

        configArguments['userSandbox'] = tarFilename
        configArguments['userFiles'] = [os.path.basename(f) for f in self.config.JobType.inputFiles]
        configArguments['InputDataset'] = self.config.Data.inputDataset
        configArguments['ProcessingVersion'] = self.config.Data.processingVersion

        # Create CMSSW config
        cmsswCfg = CMSSWConfig(config=self.config, logger=self.logger,
                               userConfig=self.config.JobType.psetName)

        # Interogate CMSSW config for output file names
        for fileList in cmsswCfg.outputFiles():
            self.logger.debug("Adding %s to list of output files" % fileList)
            configArguments['outputFiles'].extend(fileList)

        # Write out CMSSW config
        cmsswCfg.writeFile(cfgOutputName)
        result = cmsswCfg.upload(requestConfig)
        configArguments['AnalysisConfigCacheDoc'] = result[0]['DocID']
        return tarFilename, configArguments


    def validateConfig(self, config):
        """
        Validate the config file making sure required values are there
        and optional values don't conflict
        """

        result = (True, '')

        if getattr(config.JobType, 'psetName', None) is None:
            result = (False, "Missing 'JobType.psetName' parameter.")
        if not os.path.exists(config.JobType.psetName) or not os.path.isfile(config.JobType.psetName):
            result = (False, "Pset file %s missing." % config.JobType.psetName)

        return result
