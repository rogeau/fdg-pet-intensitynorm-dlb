function inorm_ihn(patient_dir, threshold)
    if nargin < 2
        threshold = 0.01;
    elseif ischar(threshold) || isstring(threshold)
        threshold = str2double(threshold);
    end

    % Remove trailing slash if exists
    patient_dir = char(strip(patient_dir, '/'));

    [parent_dir, ~, ~] = fileparts(patient_dir);
    threshold_str = strrep(num2str(threshold, '%.15g'), '.', '');

    % --- Excel file ---
    excel_file = fullfile(parent_dir, 'normalizing_factors.xlsx');
    if exist(excel_file, 'file')
        norm_table = readtable(excel_file, 'TextType', 'string');
    else
        norm_table = table(strings(0,1), strings(0,1), 'VariableNames', {'IPP','Date'});
        writetable(norm_table, excel_file);
        fprintf('Created new Excel file: %s\n', excel_file);
    end

    % --- Add dynamic column for this threshold ---
    col_name = sprintf('ihn_%s', threshold_str);
    if ~ismember(col_name, norm_table.Properties.VariableNames)
        norm_table.(col_name) = NaN(height(norm_table),1);
    end

    paths = dir(fullfile(patient_dir, '**', 's_wr_petsuv.nii'));
    template_path = 'hn_template.nii';
    Vt = spm_vol(template_path);
    template = spm_read_vols(Vt);

    qc_pdf = fullfile(parent_dir, sprintf('ihn%s_QC.pdf', threshold_str));
    if exist(qc_pdf, 'file')
        delete(qc_pdf);
    end

    for i = 1:numel(paths)
        file_path = fullfile(paths(i).folder, paths(i).name);
        Vi = spm_vol(file_path);
        img = spm_read_vols(Vi);

        mask_path = fullfile(paths(i).folder, sprintf('ihn_mask%s.nii', threshold_str));
        if ~exist(mask_path, 'file')
            warning('Mask not found: %s. Skipping.', mask_path);
            continue;
        end
        Vm = spm_vol(mask_path);
        mask = spm_read_vols(Vm) > 0.5;

        ratio_img = img ./ template;
        vals = ratio_img(mask);
        vals = vals(~isnan(vals) & ~isinf(vals));

        nbins = 1000;
        [counts, edges] = histcounts(vals, nbins);
        [~, idx] = max(counts);
        mode_val = (edges(idx) + edges(idx+1)) / 2;

        fprintf('Mode of %s: %.4f\n', paths(i).name, mode_val);

        % --- Normalize ---
        Vn = spm_vol(fullfile(paths(i).folder, 'wr_petsuv.nii'));
        img_to_norm = spm_read_vols(Vn);
        img_hn = img_to_norm / mode_val;

        Vout = Vn;
        Vout.fname = fullfile(paths(i).folder, sprintf('ihn%s_wr_petsuv.nii', threshold_str));
        spm_write_vol(Vout, img_hn);

        % --- Update Excel ---
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
            new_row.(col_name) = mode_val;
            norm_table = [norm_table; new_row];
        else
            norm_table.(col_name)(row_idx) = mode_val;
        end

        % QC: Histogram with mode line
        fig = figure('Visible','off','Position',[100 100 800 600]);
        
        % Navy blue histogram
        histogram(vals, nbins, 'EdgeColor','none', 'FaceColor',[0 0 0.5]);  % navy blue
        hold on;
        
        ylims = ylim;
        
        % Black mode line
        plot([mode_val mode_val], ylims, 'k--','LineWidth',2);  % black dashed line
        
        % Mode value text in black
        x_offset = (max(vals) - min(vals)) * 0.02; 
        text(mode_val + x_offset, ylims(2)*0.95, sprintf('Mode = %.4f', mode_val), ...
            'Color','k','FontWeight','bold','HorizontalAlignment','left');
        
        hold off;
        xlabel('SUVR');
        ylabel('Count of voxels');
        
        % Title slightly higher
        title(sprintf('Histogram Normalization - %s', [paths(i).folder paths(i).name]), ...
            'Interpreter','none', 'FontWeight','bold', 'Units','normalized', 'Position',[0.5 1.05 0]);
        
        % Remove top and right lines
        box off
        ax = gca;
        ax.XAxisLocation = 'bottom';
        ax.YAxisLocation = 'left';
        
        exportgraphics(fig, qc_pdf, 'Append', true);
        close(fig);


    end

    % --- Save Excel ---
    writetable(norm_table, excel_file);
    fprintf('✅ Normalizing factors updated: %s\n', excel_file);
    fprintf('✅ QC histograms saved: %s\n', qc_pdf);
end
