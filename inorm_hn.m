function inorm_hn(directory)
    paths = dir(fullfile(directory, '**', 's_wr_petsuv.nii'));
    template_path = 'hn_template.nii';
    mask_path = 'parenchymal_mask.nii';

    % Load template & mask
    Vt = spm_vol(template_path);
    template = spm_read_vols(Vt);
    Vm = spm_vol(mask_path);
    mask = spm_read_vols(Vm) > 0;

    % Excel bookkeeping
    excel_file = fullfile(directory, 'normalizing_factors.xlsx');
    if ~exist(excel_file, 'file')
        T = table(strings(0,1), strings(0,1), 'VariableNames', {'IPP','Date'});
        writetable(T, excel_file);
        fprintf('Created new Excel file: %s\n', excel_file);
    end
    norm_table = readtable(excel_file, 'TextType','string');

    if ~ismember('hn', norm_table.Properties.VariableNames)
        norm_table.hn = NaN(height(norm_table),1);
    end

    % QC PDF
    qc_pdf = fullfile(directory, 'hn_QC.pdf');
    if exist(qc_pdf, 'file')
        delete(qc_pdf);
    end

    % Loop over subjects
    for i = 1:length(paths)
        file_path = fullfile(paths(i).folder, paths(i).name);
        Vi = spm_vol(file_path);
        img = spm_read_vols(Vi);

        % Ratio image
        ratio_img = img ./ template;
        vals = ratio_img(mask);
        vals = vals(~isnan(vals) & ~isinf(vals));

        % Histogram mode
        nbins = 1000;
        [counts, edges] = histcounts(vals, nbins);
        [~, idx] = max(counts);
        mode_val = (edges(idx) + edges(idx+1)) / 2;

        fprintf('Mode of %s: %.4f\n', paths(i).name, mode_val);

        % Normalize PET
        path_to_norm = fullfile(paths(i).folder, 'wr_petsuv.nii');
        if ~exist(path_to_norm,'file')
            warning('PET file not found: %s', path_to_norm);
            continue;
        end
        Vn = spm_vol(path_to_norm);
        img_to_norm = spm_read_vols(Vn);

        img_hn = img_to_norm / mode_val;
        Vout = Vn;
        Vout.fname = fullfile(paths(i).folder, 'hn_wr_petsuv.nii');
        spm_write_vol(Vout, img_hn);

        % Update Excel
        [filepath_parent, ~, ~] = fileparts(file_path);
        [filepath_gdparent, parent_folder] = fileparts(filepath_parent);
        [~, gdparent_folder] = fileparts(filepath_gdparent);
        IPP = string(gdparent_folder);
        Date = string(parent_folder);

        row_idx = find(strcmp(norm_table.IPP, IPP) & strcmp(norm_table.Date, Date));
        if isempty(row_idx)
            % Add new row
            new_row = cell2table(cell(1,width(norm_table)), ...
                                 'VariableNames', norm_table.Properties.VariableNames);
            new_row.IPP = IPP;
            new_row.Date = Date;
            new_row.hn = mode_val;
            norm_table = [norm_table; new_row];
        else
            norm_table.hn(row_idx) = mode_val;
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

    % Save Excel
    writetable(norm_table, excel_file);
    fprintf('✅ Normalization factors updated in: %s\n', excel_file);
    fprintf('✅ QC PDF saved in: %s\n', qc_pdf);
end