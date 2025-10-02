function inorm_ps(input_dir)
    nii_files = dir(fullfile(input_dir, '**', 'wr_petsuv.nii'));

    gm_path = 'parenchymal_mask.nii';  % PS mask
    excel_file = fullfile(input_dir, 'normalizing_factors.xlsx');

    this_col = 'ps'; % <-- name of this script’s factor column

    % --- Load or create Excel table ---
    if exist(excel_file, 'file')
        norm_table = readtable(excel_file, 'TextType','string');
    else
        norm_table = table( ...
            strings(0,1), ... % IPP
            strings(0,1), ... % Date
            'VariableNames', {'IPP','Date'});
        writetable(norm_table, excel_file);
        fprintf('Created new Excel file: %s\n', excel_file);
    end

    % --- Ensure this script’s column exists ---
    if ~ismember(this_col, norm_table.Properties.VariableNames)
        norm_table.(this_col) = nan(height(norm_table),1);
    end

    % --- Prepare PDF for QC ---
    qc_pdf = fullfile(input_dir, 'ps_QC.pdf');
    if exist(qc_pdf, 'file')
        delete(qc_pdf);
    end

    % --- Loop over PET files ---
    for i = 1:length(nii_files)
        pet_path = fullfile(nii_files(i).folder, nii_files(i).name);

        if ~exist(pet_path, 'file') || ~exist(gm_path, 'file')
            warning('Missing PET or PS mask for %s. Skipping.', pet_path);
            continue;
        end

        fprintf('📈 Intensity Normalization... %s\n', pet_path);

        % Extract IPP (grandparent) and Date (parent)
        [filepath_parent, ~, ~] = fileparts(pet_path);  
        [filepath_gdparent, parent_folder] = fileparts(filepath_parent); 
        [~, gdparent_folder] = fileparts(filepath_gdparent); 
        IPP = string(gdparent_folder);
        Date = string(parent_folder);

        % --- Load data ---
        Vp  = spm_vol(pet_path);
        Ypet = spm_read_vols(Vp);

        Vps = spm_vol(gm_path);
        Yps = spm_read_vols(Vps);

        % --- Build PS mask ---
        mask = Yps > 0.5;

        % --- Compute mean in mask ---
        ps_vals = Ypet(mask > 0);
        mean_val = mean(ps_vals(:), 'omitnan');

        if mean_val == 0 || isnan(mean_val)
            warning('⚠️ PS mean is zero or NaN in %s. Skipping.', pet_path);
            continue;
        end

        % --- Normalize PET ---
        norm_pet = Ypet ./ mean_val;
        Vn = Vp;
        Vn.fname = fullfile(nii_files(i).folder, 'ps_wr_petsuv.nii');
        spm_write_vol(Vn, norm_pet);

        fprintf('Subject: %s | Mean PS uptake: %.4f\n', nii_files(i).folder, mean_val);

        % --- Update Excel ---
        row_idx = find(strcmp(norm_table.IPP, IPP) & strcmp(norm_table.Date, Date));
        if isempty(row_idx)
            new_row = cell2table(cell(1, width(norm_table)), ...
                                 'VariableNames', norm_table.Properties.VariableNames);
            new_row.IPP = IPP;
            new_row.Date = Date;
            new_row.(this_col) = mean_val;
            norm_table = [norm_table; new_row];
        else
            norm_table.(this_col)(row_idx) = mean_val;
        end

        % --- QC visualization (middle axial slice) ---
        [~,~,z] = ind2sub(size(mask), find(mask));
        if isempty(z)
            warning('Empty PS ROI in %s. Skipping QC.', pet_path);
            continue;
        end
        z_mid = round(mean(z));

        pet_slice = rot90(squeeze(Ypet(:,:,z_mid)),1);
        mask_slice = rot90(squeeze(mask(:,:,z_mid)),1);

        overlay = mat2gray(pet_slice);
        overlay_rgb = repmat(overlay, [1 1 3]);
        overlay_rgb(:,:,1) = overlay_rgb(:,:,1) + 0.5*mask_slice;

        fig = figure('Visible','off','Position',[100 100 1200 400]);
        colormap gray;

        subplot(1,3,1);
        imagesc(pet_slice); axis image off;
        title('PET');

        subplot(1,3,2);
        imagesc(mask_slice); axis image off;
        title('PS Mask');

        subplot(1,3,3);
        imagesc(overlay_rgb); axis image off;
        title('Overlay (PET + PS)');

        sgtitle(sprintf('QC: %s (slice %d)', nii_files(i).folder, z_mid), 'Interpreter','none');

        exportgraphics(fig, qc_pdf, 'Append', true);
        close(fig);
    end

    % --- Save updated Excel table ---
    writetable(norm_table, excel_file);
    fprintf('✅ Normalization factors updated in: %s\n', excel_file);
    fprintf('✅ QC PDF saved in: %s\n', qc_pdf);
end
