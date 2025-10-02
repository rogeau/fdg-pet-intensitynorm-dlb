function inorm_wm(directory)
    paths = dir(fullfile(directory, '**', 'wr_petsuv.nii'));

    excel_file = fullfile(directory, 'normalizing_factors.xlsx');
    if ~exist(excel_file, 'file')
        T = table(strings(0,1), strings(0,1), 'VariableNames', {'IPP','Date'});
        writetable(T, excel_file);
        fprintf('Created new Excel file: %s\n', excel_file);
    end
    norm_table = readtable(excel_file, 'TextType','string');

    if ~ismember('wm', norm_table.Properties.VariableNames)
        norm_table.wm = NaN(height(norm_table),1);
    end

    qc_pdf = fullfile(directory, 'wm_QC.pdf');
    if exist(qc_pdf, 'file')
        delete(qc_pdf);
    end

    for i = 1:length(paths)
        pet_path = fullfile(paths(i).folder, paths(i).name);
        wm_path  = fullfile(paths(i).folder, 'mri', 'wp2mri.nii');

        if ~exist(pet_path,'file') || ~exist(wm_path,'file')
            warning('Missing PET or WM file in %s, skipping.', paths(i).folder);
            continue;
        end

        % -----------------------------------------------------------------
        % Build eroded WM mask
        Vw = spm_vol(wm_path);
        Yw = spm_read_vols(Vw);
        mask = Yw > 0.7;
        mask = imerode(mask, ones(3,3,3));

        Vm = Vw;
        Vm.fname = fullfile(paths(i).folder, 'mri', 'wm_mask_eroded.nii');
        spm_write_vol(Vm, double(mask));

        % -----------------------------------------------------------------
        % Normalize PET
        Vp  = spm_vol(pet_path);
        Ypet = spm_read_vols(Vp);
        wm_vals = Ypet(mask > 0);
        mean_val = mean(wm_vals(:),'omitnan');

        norm_pet = Ypet ./ mean_val;
        Vn = Vp;
        Vn.fname = fullfile(paths(i).folder, 'wm_wr_petsuv.nii');
        spm_write_vol(Vn, norm_pet);

        fprintf('Subject: %s | Mean WM uptake: %.4f\n', paths(i).folder, mean_val);

        % -----------------------------------------------------------------
        % Update Excel table
        [filepath_parent, ~, ~] = fileparts(pet_path);
        [filepath_gdparent, parent_folder] = fileparts(filepath_parent);
        [~, gdparent_folder] = fileparts(filepath_gdparent);
        IPP = string(gdparent_folder);
        Date = string(parent_folder);

        row_idx = find(strcmp(norm_table.IPP, IPP) & strcmp(norm_table.Date, Date));
        if isempty(row_idx)
            % New row
            new_row = cell2table(cell(1,width(norm_table)), ...
                                 'VariableNames', norm_table.Properties.VariableNames);
            new_row.IPP = IPP;
            new_row.Date = Date;
            new_row.wm = mean_val;
            norm_table = [norm_table; new_row];
        else
            % Update row
            norm_table.wm(row_idx) = mean_val;
        end

        % -----------------------------------------------------------------
        % QC visualization (middle axial slice)
        [~,~,z] = ind2sub(size(mask), find(mask));
        if isempty(z)
            warning('Empty WM ROI in %s. Skipping QC figure.', pet_path);
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
        title('WM Mask');

        subplot(1,3,3);
        imagesc(overlay_rgb); axis image off;
        title('Overlay (PET + WM)');

        sgtitle(sprintf('QC: %s (slice %d)', paths(i).folder, z_mid), 'Interpreter','none');

        exportgraphics(fig, qc_pdf, 'Append', true);
        close(fig);
    end

    % Save updated Excel
    writetable(norm_table, excel_file);
    fprintf('✅ Normalization factors updated in: %s\n', excel_file);
    fprintf('✅ QC PDF saved in: %s\n', qc_pdf);
end