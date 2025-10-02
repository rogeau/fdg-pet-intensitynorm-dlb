function masks_ips(patient_dir, control_dir, threshold)
    if nargin < 3
        threshold = 0.01;
    elseif ischar(threshold) || isstring(threshold)
        threshold = str2double(threshold);
    end

    threshold_str = strrep(num2str(threshold, '%.15g'), '.', '');
    excel_file = fullfile(fileparts(patient_dir), 'masks_voxel.xlsx');
    
    if exist(excel_file, 'file')
        voxel_table = readtable(excel_file, 'TextType','string');
    else
        voxel_table = table(strings(0,1), strings(0,1), 'VariableNames', {'IPP','Date'});
        writetable(voxel_table, excel_file);
        fprintf('Created new Excel file: %s\n', excel_file);
    end

    ips_col = sprintf('ips_%s', threshold_str);
    if ~ismember(ips_col, voxel_table.Properties.VariableNames)
        voxel_table.(ips_col) = NaN(height(voxel_table),1);
    end
    
    original_dir = pwd; 

    spm('defaults', 'PET');
    spm_get_defaults('cmdline', true);
    
    patient_paths = dir(fullfile(patient_dir, '**', 's_ps_wr_petsuv.nii'));
    control_paths = dir(fullfile(control_dir, '**', 's_ps_wr_petsuv.nii'));
    control_files = strcat(fullfile({control_paths.folder}, {control_paths.name}));

    for d = 1:numel(patient_paths)
        pet_file = fullfile(patient_paths(d).folder, patient_paths(d).name);
        fprintf('⚙️ Creating individual mask for file: %s\n', pet_file);
        pet_file = [pet_file ',1'];

        parent_folder = patient_paths(d).folder;
        target_folder = fullfile(parent_folder, sprintf('ips_mask_analysis%s', threshold_str));       
        if exist(target_folder,'dir')
            rmdir(target_folder,'s');
        end
        mkdir(target_folder);

        clear matlabbatch

        % 1. Factorial design
        matlabbatch{1}.spm.stats.factorial_design.dir = {target_folder};
        matlabbatch{1}.spm.stats.factorial_design.des.t2.scans1 = control_files';
        matlabbatch{1}.spm.stats.factorial_design.des.t2.scans2 = {pet_file};
        matlabbatch{1}.spm.stats.factorial_design.des.t2.dept = 0;
        matlabbatch{1}.spm.stats.factorial_design.des.t2.variance = 1;
        matlabbatch{1}.spm.stats.factorial_design.des.t2.gmsca = 0;
        matlabbatch{1}.spm.stats.factorial_design.des.t2.ancova = 0;
        matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});
        matlabbatch{1}.spm.stats.factorial_design.multi_cov = struct('files', {}, 'iCFI', {}, 'iCC', {});
        matlabbatch{1}.spm.stats.factorial_design.masking.tm.tm_none = 1;
        matlabbatch{1}.spm.stats.factorial_design.masking.im = 0;
        matlabbatch{1}.spm.stats.factorial_design.masking.em = {'parenchymal_mask.nii,1'};
        matlabbatch{1}.spm.stats.factorial_design.globalc.g_mean = 1;
        matlabbatch{1}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;
        matlabbatch{1}.spm.stats.factorial_design.globalm.glonorm = 2;

        matlabbatch{2}.spm.stats.fmri_est.spmmat(1) = cfg_dep('Factorial design specification: SPM.mat File', ...
            substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), ...
            substruct('.','spmmat'));
        matlabbatch{2}.spm.stats.fmri_est.write_residuals = 0;
        matlabbatch{2}.spm.stats.fmri_est.method.Classical = 1;

        matlabbatch{3}.spm.stats.con.spmmat(1) = cfg_dep('Model estimation: SPM.mat File', ...
            substruct('.','val', '{}',{2}, '.','val', '{}',{1}, '.','val', '{}',{1}), ...
            substruct('.','spmmat'));
        matlabbatch{3}.spm.stats.con.consess{1}.fcon.name = 'Hypo/hyper';
        matlabbatch{3}.spm.stats.con.consess{1}.fcon.weights = [1 -1];
        matlabbatch{3}.spm.stats.con.consess{1}.fcon.sessrep = 'none';
        matlabbatch{3}.spm.stats.con.delete = 1;

        matlabbatch{4}.spm.stats.results.spmmat(1) = cfg_dep('Contrast Manager: SPM.mat File', ...
            substruct('.','val', '{}',{3}, '.','val', '{}',{1}, '.','val', '{}',{1}), ...
            substruct('.','spmmat'));
        matlabbatch{4}.spm.stats.results.conspec.titlestr = '';
        matlabbatch{4}.spm.stats.results.conspec.contrasts = 1;
        matlabbatch{4}.spm.stats.results.conspec.threshdesc = 'none';
        matlabbatch{4}.spm.stats.results.conspec.thresh = threshold;
        matlabbatch{4}.spm.stats.results.conspec.extent = 0;
        matlabbatch{4}.spm.stats.results.conspec.conjunction = 1;
        matlabbatch{4}.spm.stats.results.conspec.mask.none = 1;
        matlabbatch{4}.spm.stats.results.units = 1;
        matlabbatch{4}.spm.stats.results.export{1}.binary.basename = 'hypo_hyper_mask';
        matlabbatch{4}.spm.stats.results.export{2}.ps = true;

        original_mask = fullfile(target_folder, 'mask.nii');
        hypo_hyper_mask = fullfile(target_folder, 'spmF_0001_hypo_hyper_mask.nii');

        matlabbatch{5}.spm.util.imcalc.input = {original_mask; hypo_hyper_mask};
        matlabbatch{5}.spm.util.imcalc.output = sprintf('ips_mask%s', threshold_str);
        matlabbatch{5}.spm.util.imcalc.outdir = {parent_folder};
        matlabbatch{5}.spm.util.imcalc.expression = 'i1 - i2';
        matlabbatch{5}.spm.util.imcalc.var = struct('name', {}, 'value', {});
        matlabbatch{5}.spm.util.imcalc.options.dmtx = 0;
        matlabbatch{5}.spm.util.imcalc.options.mask = -1;
        matlabbatch{5}.spm.util.imcalc.options.interp = 1;
        matlabbatch{5}.spm.util.imcalc.options.dtype = 2;

        spm_jobman('run', matlabbatch);
        cd(original_dir);


        original_mask = fullfile(target_folder, 'mask.nii');
        ips_mask = fullfile(parent_folder, sprintf('ips_mask%s.nii', threshold_str));
        Vorig = spm_vol(original_mask);
        Yorig = spm_read_vols(Vorig) > 0;
        Vips = spm_vol(ips_mask);
        Yips = spm_read_vols(Vips) > 0;

        vox_removed = nnz(Yorig) - nnz(Yips);  % number of voxels removed

        % --- Extract IPP and Date ---
        [filepath_parent, ~, ~] = fileparts(pet_file);
        [filepath_gdparent, parent_name] = fileparts(filepath_parent);
        [~, gdparent_name] = fileparts(filepath_gdparent);
        IPP = string(gdparent_name);
        Date = string(parent_name);

        % --- Update Excel table ---
        row_idx = find(strcmp(voxel_table.IPP, IPP) & strcmp(voxel_table.Date, Date));
        if isempty(row_idx)
            new_row = cell2table(cell(1,width(voxel_table)), 'VariableNames', voxel_table.Properties.VariableNames);
            new_row.IPP = IPP;
            new_row.Date = Date;
            new_row.(ips_col) = vox_removed;
            voxel_table = [voxel_table; new_row];
        else
            voxel_table.(ips_col)(row_idx) = vox_removed;
        end
    end

    writetable(voxel_table, excel_file);
    fprintf('✅ Masks voxel table updated: %s\n', excel_file);
end