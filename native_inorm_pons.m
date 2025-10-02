function native_inorm_pons(directory, filename)
    % Define output PDF in the main directory
    outputPDF = fullfile(directory, 'pons_QC.pdf');
    
    % If file exists, delete it to start fresh
    if isfile(outputPDF)
        delete(outputPDF);
    end
    
    % Find all matching files recursively
    files = dir(fullfile(directory, '**', filename));
    fullPaths = fullfile({files.folder}, {files.name})';
    
    for i = 1:numel(fullPaths)
        fullPath = fullPaths{i};
        
        % Get parent folders
        [parent1, ~, ~] = fileparts(fullPath);
        [parent2, ~, ~] = fileparts(parent1);
        [parent3, ~, ~] = fileparts(parent2);
        [~, folder1] = fileparts(parent1);
        [~, folder2] = fileparts(parent2);
        [~, folder3] = fileparts(parent3);
        
        % Build Pons mask path
        pons_path = fullfile('results_assembly', ...
            ['wfu_pons_native_' folder3 '_' folder2 '_' folder1 '.nii.gz']);

        if ~isfile(pons_path)
            warning('Pons mask not found for %s', fullPath);
            continue;
        end
        
        % Load image and mask
        imgInfo = niftiinfo(fullPath);
        imgData = niftiread(imgInfo);
        maskData = niftiread(pons_path);
        
        % Compute mean inside Pons mask
        maskIndices = maskData > 0;
        meanValue = mean(double(imgData(maskIndices)));
        
        % Normalize the image
        normData = double(imgData) / meanValue;
        normDataCast = cast(normData, class(imgData)); 
        
        % Save normalized image in same directory with new name
        [~, imgName, ~] = fileparts(fullPath);
        newFileName = fullfile(parent1, ['pons_' imgName '.nii.gz']);
        
        niftiwrite(normDataCast, newFileName, imgInfo, 'Compressed', true);
        
        fprintf('Normalized image saved: %s\n', newFileName);
        
        %% ✅ QC Step: Sagittal slice through middle of Pons mask
        
        % Find all voxel coordinates of the Pons mask
        [rows, cols, slices] = ind2sub(size(maskData), find(maskData > 0));
        
        % Sagittal slice index = middle of mask along X-axis
        centerX = round(median(rows));  % correct: rows = X-axis
        
        % Extract sagittal slice (Y × Z)
        sagittalImage = squeeze(normData(centerX, :, :));
        sagittalMask  = squeeze(maskData(centerX, :, :));
        
        % Flip vertically for correct orientation
        sagittalImage = flipud(sagittalImage');
        sagittalMask  = flipud(sagittalMask');
        
        % Display and overlay
        fig = figure('Visible', 'off');
        imshow(sagittalImage, [], 'Colormap', gray); hold on;
        maskOutlineSagittal = bwperim(sagittalMask > 0);
        h = imshow(cat(3, ones(size(maskOutlineSagittal)), zeros(size(maskOutlineSagittal)), zeros(size(maskOutlineSagittal)))); % red overlay
        set(h, 'AlphaData', maskOutlineSagittal * 0.5);
        title(['Sagittal Slice (Middle of Pons Mask) - ' imgName], 'Interpreter', 'none');
        hold off;
        
        % Append to PDF
        exportgraphics(fig, outputPDF, 'ContentType', 'vector', 'Append', true);
        close(fig);
        
        fprintf('Appended sagittal QC image (mask middle) for %s to %s\n', imgName, outputPDF);



    end
    
    fprintf('✅ All QC images saved in one PDF: %s\n', outputPDF);
end
