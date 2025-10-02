function inorm_pons(directory, pet, wmmap)
    spm('defaults','PET');
    spm_jobman('initcfg');

    folders = genpath(directory);
    folder_list = strsplit(folders, pathsep);

    excel_file = fullfile(directory, 'normalizing_factors.xlsx');
    this_col = 'pons'; % this script’s factor column

    % --- Load or create Excel table ---
    if exist(excel_file, 'file')
        norm_table = readtable(excel_file, 'TextType', 'string');
    else
        % Create empty table with only IPP and Date
        norm_table = table(strings(0,1), strings(0,1), ...
                           'VariableNames', {'IPP','Date'});
        writetable(norm_table, excel_file);
        fprintf('Created new Excel file: %s\n', excel_file);
    end

    % --- Ensure ID columns are string ---
    if ~ismember('IPP', norm_table.Properties.VariableNames)
        norm_table.IPP = strings(height(norm_table),1);
    else
        norm_table.IPP = string(norm_table.IPP);
    end
    if ~ismember('Date', norm_table.Properties.VariableNames)
        norm_table.Date = strings(height(norm_table),1);
    else
        norm_table.Date = string(norm_table.Date);
    end

    % --- Ensure this script’s column exists ---
    if ~ismember(this_col, norm_table.Properties.VariableNames)
        norm_table.(this_col) = nan(height(norm_table),1);
    end

    % --- QC PDF file ---
    qc_pdf = fullfile(directory, 'pons_QC.pdf');
    if exist(qc_pdf,'file')
        delete(qc_pdf);
    end

    % --- Loop over all subfolders ---
    for i = 1:length(folder_list)
        folder = folder_list{i};
        if isempty(folder)
            continue;
        end

        pet_path = fullfile(folder, pet);
        wm_path  = fullfile(folder, 'mri', wmmap);

        if exist(pet_path,'file') && exist(wm_path,'file')
            fprintf('📈 Intensity normalization: %s\n', folder);

            %------------------------------------------------------------------
            % 1. Reslice pons atlas to WM space
            clear matlabbatch
            matlabbatch{1}.spm.spatial.coreg.write.ref    = {wm_path};
            matlabbatch{1}.spm.spatial.coreg.write.source = {'wfu_pons.nii'}; % path to atlas
            matlabbatch{1}.spm.spatial.coreg.write.roptions.interp = 0; % nearest neighbour
            matlabbatch{1}.spm.spatial.coreg.write.roptions.wrap   = [0 0 0];
            matlabbatch{1}.spm.spatial.coreg.write.roptions.mask   = 0;
            matlabbatch{1}.spm.spatial.coreg.write.roptions.prefix = 'r_';
            spm_jobman('run',matlabbatch);

            [~,n,ext] = fileparts('wfu_pons.nii');
            spm_out   = fullfile(pwd, ['r_' n ext]);        
            resliced_pons = fullfile(folder, ['r_' n ext]); 
            
            if exist(spm_out,'file')
                movefile(spm_out, resliced_pons);
            end

            %------------------------------------------------------------------
            % 2. Threshold WM and intersect with pons
            Vwm   = spm_vol(wm_path);
            Ywm   = spm_read_vols(Vwm);
            Vpons = spm_vol(resliced_pons);
            Ypons = spm_read_vols(Vpons);

            WMmask = Ywm > 0.2;
            ROI    = WMmask & (Ypons > 0.5);

            % Save ROI
            roi_file   = fullfile(folder, 'ROI_pons_wm.nii');
            Vroi       = Vwm;
            Vroi.fname = roi_file;
            spm_write_vol(Vroi,double(ROI));

            %------------------------------------------------------------------
            % 3. Compute mean PET value in ROI
            Vpet = spm_vol(pet_path);
            Ypet = spm_read_vols(Vpet);
            roi_vals = Ypet(ROI);
            mean_ref = mean(roi_vals(~isnan(roi_vals) & roi_vals>0));

            %------------------------------------------------------------------
            % 4. Normalize PET by mean_ref and save
            Ypet_norm  = Ypet / mean_ref;
            Vnorm      = Vpet;
            Vnorm.fname = fullfile(folder, ['pons_' pet]);
            spm_write_vol(Vnorm,Ypet_norm);

            fprintf('✅ Done %s → mean=%.3f\n', folder, mean_ref);

            %------------------------------------------------------------------
            % 5. Update Excel file
            [filepath_parent, ~, ~] = fileparts(pet_path);        
            [filepath_gdparent, parent_folder] = fileparts(filepath_parent); 
            [~, gdparent_folder] = fileparts(filepath_gdparent);             
            IPP = string(gdparent_folder);
            Date = string(parent_folder);

            row_idx = find(strcmp(norm_table.IPP, IPP) & strcmp(norm_table.Date, Date));

            if isempty(row_idx)
                % Append new row with NaN for all factor columns
                new_row = cell2table(cell(1, width(norm_table)), ...
                                     'VariableNames', norm_table.Properties.VariableNames);
                % Fill NaN for all factor columns
                for c = 1:width(norm_table)
                    if ~ismember(norm_table.Properties.VariableNames{c}, {'IPP','Date'})
                        new_row.(norm_table.Properties.VariableNames{c}) = NaN;
                    end
                end
                % Fill identifying info + this factor
                new_row.IPP = IPP;
                new_row.Date = Date;
                new_row.(this_col) = mean_ref;
                % Append
                norm_table = [norm_table; new_row];
            else
                % Update existing row
                norm_table.(this_col)(row_idx) = mean_ref;
            end

            %------------------------------------------------------------------
            % 6. QC Visualization
            [~,~,z] = ind2sub(size(ROI), find(ROI));
            if isempty(z)
                warning('No ROI found in %s. Skipping QC figure.', folder);
                continue;
            end
            z_mid   = round(mean(z));  
            
            pet_slice  = rot90(squeeze(Ypet(:,:,z_mid)),1);
            mask_slice = rot90(squeeze(ROI(:,:,z_mid)),1);
            
            overlay = mat2gray(pet_slice);
            overlay_rgb = repmat(overlay, [1 1 3]);
            overlay_rgb(:,:,1) = overlay_rgb(:,:,1) + 0.5*mask_slice;
            
            fig = figure('Visible','off','Position',[100 100 1200 400]);
            colormap gray;
            
            subplot(1,3,1); imagesc(pet_slice); axis image off; title('PET');
            subplot(1,3,2); imagesc(mask_slice); axis image off; title('ROI Mask');
            subplot(1,3,3); imagesc(overlay_rgb); axis image off; title('Overlay');
            
            sgtitle(sprintf('QC: %s (slice %d)', folder, z_mid),'Interpreter','none');
            exportgraphics(fig, qc_pdf, 'Append', true);
            close(fig);
        end
    end

    % --- Save updated table ---
    writetable(norm_table, excel_file);
    fprintf('✅ All QC figures saved in: %s\n', qc_pdf);
    fprintf('✅ Normalization factors updated in: %s\n', excel_file);
end
