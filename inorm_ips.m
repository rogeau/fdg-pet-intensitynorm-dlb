function inorm_ips(patient_dir, threshold)
    if nargin < 2
        threshold = 0.01;
    elseif ischar(threshold) || isstring(threshold)
        threshold = str2double(threshold);
    end

    [parent_dir, ~, ~] = fileparts(patient_dir);
    threshold_str = strrep(num2str(threshold, '%.15g'), '.', '');
    excel_file = fullfile(parent_dir, 'normalizing_factors.xlsx');

    % --- Load or create Excel table ---
    if exist(excel_file, 'file')
        norm_table = readtable(excel_file, 'TextType','string');
    else
        norm_table = table(strings(0,1), strings(0,1), 'VariableNames', {'IPP','Date'});
        writetable(norm_table, excel_file);
        fprintf('Created new Excel file: %s\n', excel_file);
    end

    % --- Add dynamic column for this threshold ---
    col_name = sprintf('ips_%s', threshold_str);
    if ~ismember(col_name, norm_table.Properties.VariableNames)
        norm_table.(col_name) = NaN(height(norm_table),1);
    end

    nii_files = dir(fullfile(patient_dir, '**', 'wr_petsuv.nii'));
    qc_pdf = fullfile(fileparts(parent_dir), sprintf('ips%s_QC.pdf', threshold_str));
    
    if exist(qc_pdf, 'file')
        delete(qc_pdf);
    end

    for i = 1:length(nii_files)
        file_path = fullfile(nii_files(i).folder, nii_files(i).name);
        mask_path = fullfile(nii_files(i).folder, sprintf('ips_mask%s.nii', threshold_str));

        if ~exist(file_path, 'file')
            warning('File not found: %s. Skipping.', file_path);
            continue;
        end
        if ~exist(mask_path, 'file')
            warning('Mask not found: %s. Skipping.', mask_path);
            continue;
        end

        fprintf('📈 Iterative Intensity Normalization... %s\n', file_path);

        Vp = spm_vol(file_path);
        Ypet = spm_read_vols(Vp);

        Vm = spm_vol(mask_path);
        mask = spm_read_vols(Vm) > 0.5;

        mask_mean = mean(Ypet(mask), 'omitnan');

        if mask_mean == 0 || isnan(mask_mean)
            warning('⚠️ Mask mean is zero or NaN in %s. Skipping.', file_path);
            continue;
        else
            norm_pet = Ypet ./ mask_mean;
            Vn = Vp;
            [~, name, ext] = fileparts(nii_files(i).name);
            Vn.fname = fullfile(nii_files(i).folder, [sprintf('ips%s_', threshold_str) name ext]);
            spm_write_vol(Vn, norm_pet);
        end

        % --- Update Excel table ---
        [filepath_parent, ~, ~] = fileparts(file_path);
        [filepath_gdparent, parent_folder] = fileparts(filepath_parent);
        [~, gdparent_folder] = fileparts(filepath_gdparent);

        IPP = string(gdparent_folder);
        Date = string(parent_folder);

        row_idx = find(strcmp(norm_table.IPP, IPP) & strcmp(norm_table.Date, Date));
        if isempty(row_idx)
            new_row = cell2table(cell(1,width(norm_table)), 'VariableNames', norm_table.Properties.VariableNames);
            new_row.IPP = IPP;
            new_row.Date = Date;
            new_row.(col_name) = mask_mean;
            norm_table = [norm_table; new_row];
        else
            norm_table.(col_name)(row_idx) = mask_mean;
        end

        % --- QC visualization (middle axial slice of ROI) ---
        [~,~,z] = ind2sub(size(mask), find(mask));
        if isempty(z)
            warning('Empty IPS ROI in %s. Skipping QC.', file_path);
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
        title('IPS Mask');

        subplot(1,3,3);
        imagesc(overlay_rgb); axis image off;
        title('Overlay (PET + IPS)');

        sgtitle(sprintf('QC: %s (slice %d)', nii_files(i).folder, z_mid), 'Interpreter','none');

        exportgraphics(fig, qc_pdf, 'Append', true);
        close(fig);

    end

    % --- Save Excel table ---
    writetable(norm_table, excel_file);
    fprintf('✅ Normalizing factors updated in: %s\n', excel_file);
    fprintf('✅ QC PDF saved in: %s\n', qc_pdf);
end