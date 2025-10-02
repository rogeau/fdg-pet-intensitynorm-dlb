% === PARAMETERS ===
deffn = 'shoot_cat12segment/DLB/4305049247/20160906/mri/y_mri.nii';     % your deformation field     % output (SPM will add w prefix usually)
interp = 4;                       % 4 = cubic (use 0 for labels)

% === Read header of deformation image ===
V = spm_vol(deffn);
dim = V.dim;               % [X Y Z] e.g. [112 137 112]
M = V.mat;                 % voxel-to-world affine

% compute world coordinates of the 8 corners to get exact bounding box:
corners_vox = [
    1       1       1;
    dim(1)  1       1;
    1       dim(2)  1;
    1       1       dim(3);
    dim(1)  dim(2)  1;
    dim(1)  1       dim(3);
    1       dim(2)  dim(3);
    dim(1)  dim(2)  dim(3);
];
corners_world = (M * [corners_vox'; ones(1,8)])';
% bounding box = [xmin ymin zmin; xmax ymax zmax]
bb = [min(corners_world(:,1:3),[],1); max(corners_world(:,1:3),[],1)];

% voxel size: absolute values of diagonal of affine (row lengths)
vox = abs([norm(M(1,1:3)), norm(M(2,1:3)), norm(M(3,1:3))]);

% Print to verify
disp('Computed bounding box (bb):'); disp(bb);
disp('Voxel sizes (vox):'); disp(vox);
disp(['Deformation image dim: ', num2str(dim)]);