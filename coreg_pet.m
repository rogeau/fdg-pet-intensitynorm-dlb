function coreg_pet(directory)
    folders = genpath(directory);
    folder_list = strsplit(folders, pathsep);

    for i = 1:length(folder_list)
        folder = folder_list{i};
        if isempty(folder)
            continue;
        end

        pet_path = fullfile(folder, 'petsuv.nii');
        mri_path = fullfile(folder, 'mri.nii');

        if exist(pet_path, 'file') && exist(mri_path, 'file')
            fprintf('Coregistering PET to MRI in folder: %s\n', folder);

            matlabbatch = {};

            matlabbatch{1}.spm.spatial.coreg.estwrite.ref = {mri_path};
            matlabbatch{1}.spm.spatial.coreg.estwrite.source = {pet_path};
            matlabbatch{1}.spm.spatial.coreg.estwrite.other = {''};
            matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.cost_fun = 'nmi';
            matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.sep = [4 2];
            matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.tol = ...
                [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];
            matlabbatch{1}.spm.spatial.coreg.estwrite.eoptions.fwhm = [7 7];
            matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.interp = 4;
            matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.wrap = [0 0 0];
            matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.mask = 0;
            matlabbatch{1}.spm.spatial.coreg.estwrite.roptions.prefix = 'r_';

            spm('defaults', 'PET');
            spm_jobman('run', matlabbatch);
        end
    end
end
