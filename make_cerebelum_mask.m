function make_cerebelum_mask(templatePath)
    % Hardcoded paths
    aalPath = 'aal.nii';
    maskPath = 'aal_cerebellum.nii';
    
    % Initialize SPM (if not already)
    spm('defaults','pet');
    spm_jobman('initcfg');
    
    % ---------------------------------------------------------------------
    % Step 1: Coregister/reslice AAL to template
    % ---------------------------------------------------------------------
    matlabbatch = [];
    matlabbatch{1}.spm.spatial.coreg.write.ref = {templatePath};
    matlabbatch{1}.spm.spatial.coreg.write.source = {aalPath};
    matlabbatch{1}.spm.spatial.coreg.write.roptions.interp = 0; % nearest neighbor
    matlabbatch{1}.spm.spatial.coreg.write.roptions.wrap = [0 0 0];
    matlabbatch{1}.spm.spatial.coreg.write.roptions.mask = 0;
    matlabbatch{1}.spm.spatial.coreg.write.roptions.prefix = 'r_'; % resliced output
    
    spm_jobman('run', matlabbatch);
    
    % Resliced file path
    [pathstr,name,ext] = fileparts(aalPath);
    reslicedPath = fullfile(pathstr, ['r_' name ext]);
    
    % ---------------------------------------------------------------------
    % Step 2: Load resliced atlas
    % ---------------------------------------------------------------------
    aalVol = niftiread(reslicedPath);
    aalInfo = niftiinfo(reslicedPath);
    
    % Define cerebellum regions (Cerebelum III-VI + vermis)
    regions = [95:100 109:116];
    
    % Create binary mask
    mask = ismember(aalVol, regions);
    
    % Save binary mask in template space
    niftiwrite(uint8(mask), maskPath, aalInfo);
    
    disp(['Binary mask saved as ' maskPath]);
end
