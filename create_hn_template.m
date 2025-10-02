function create_hn_template(directory)
    control_paths = dir(fullfile(directory, '**', 'wr_petsuv.nii'));
    nFiles = length(control_paths);

    if nFiles == 0
        error('No wr_petsuv.nii files found in the specified directory.');
    end

    V = spm_vol(fullfile(control_paths(2).folder, control_paths(2).name));
    img_sum = zeros(V.dim);

    for i = 1:nFiles
        file_path = fullfile(control_paths(i).folder, control_paths(i).name);
        Vi = spm_vol(file_path);
        img = spm_read_vols(Vi);
        img(isnan(img)) = 0;
        img_sum = img_sum + img;
    end

    img_avg = img_sum / nFiles;

    Vout = V;
    Vout.fname = fullfile('hn_template.nii');
    spm_write_vol(Vout, img_avg);

    fprintf('Average template saved as %s\n', Vout.fname);
end
