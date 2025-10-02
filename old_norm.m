function old_norm(directory)
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
            fprintf('Old normalising PET to MRI in folder: %s\n', folder);
            matlabbatch{1}.spm.tools.oldnorm.estwrite.subj.source = {mri_path};
            matlabbatch{1}.spm.tools.oldnorm.estwrite.subj.wtsrc = '';
            matlabbatch{1}.spm.tools.oldnorm.estwrite.subj.resample = {mri_path
                                                                       r_pet_path
                                                                       gm_path
                                                                       wm_path
                                                                       };

            matlabbatch{1}.spm.tools.oldnorm.estwrite.eoptions.template = {'/home/arogeau/Desktop/spm12/toolbox/OldNorm/T1.nii,1'};
            matlabbatch{1}.spm.tools.oldnorm.estwrite.eoptions.weight = '';
            matlabbatch{1}.spm.tools.oldnorm.estwrite.eoptions.smosrc = 8;
            matlabbatch{1}.spm.tools.oldnorm.estwrite.eoptions.smoref = 0;
            matlabbatch{1}.spm.tools.oldnorm.estwrite.eoptions.regtype = 'mni';
            matlabbatch{1}.spm.tools.oldnorm.estwrite.eoptions.cutoff = 25;
            matlabbatch{1}.spm.tools.oldnorm.estwrite.eoptions.nits = 16;
            matlabbatch{1}.spm.tools.oldnorm.estwrite.eoptions.reg = 1;
            matlabbatch{1}.spm.tools.oldnorm.estwrite.roptions.preserve = 0;
            matlabbatch{1}.spm.tools.oldnorm.estwrite.roptions.bb = [-78 -112 -70
                                                                     78 76 85];
            matlabbatch{1}.spm.tools.oldnorm.estwrite.roptions.vox = [2 2 2];
            matlabbatch{1}.spm.tools.oldnorm.estwrite.roptions.interp = 1;
            matlabbatch{1}.spm.tools.oldnorm.estwrite.roptions.wrap = [0 0 0];
            matlabbatch{1}.spm.tools.oldnorm.estwrite.roptions.prefix = 'w_';
            spm_jobman('run', matlabbatch);
        end
    end
end