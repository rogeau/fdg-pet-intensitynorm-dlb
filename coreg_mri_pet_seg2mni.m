function coreg_mri_pet_seg2mni(directory)
    folders = genpath(directory);
    folder_list = strsplit(folders, pathsep);
    spm('defaults', 'PET');
    spm_jobman('initcfg');

    for i = 1:length(folder_list)
        folder = folder_list{i};
        if isempty(folder)
            continue;
        end

        mri_path = fullfile(folder, 'mri.nii');
        r_pet_path = fullfile(folder, 'r_pet.nii');
        gm_path = fullfile(folder, 'mri', 'hybrid_gm_map.nii');
        wm_path = fullfile(folder, 'mri', 'hybrid_wm_map.nii');

        if exist(mri_path, 'file') && exist(r_pet_path, 'file') && exist(gm_path, 'file') && exist(wm_path, 'file')
            fprintf('Coregistering PET to MRI in folder: %s\n', folder);

            matlabbatch = {};

            matlabbatch{1}.spm.spatial.coreg.estwrite.ref = {'/home/ar/spm/toolbox/OldNorm/T1.nii,1'};
            matlabbatch{1}.spm.spatial.coreg.estwrite.source = {mri_path};
            matlabbatch{1}.spm.spatial.coreg.estwrite.other = {
                                                                r_pet_path,
                                                                gm_path,
                                                                wm_path
                                                               };
            matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.cost_fun = 'nmi';
            matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.sep = [4 2];
            matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];
            matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.fwhm = [7 7];
            matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.interp = 4;
            matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.wrap = [0 0 0];
            matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.mask = 0;
            matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.prefix = 'r_mni_';

            spm_jobman('run', matlabbatch);
        end
    end
end