from nilearn import plotting

volume_file = 'mni152.nii'

# Left lateral
plotting.plot_anat(
    volume_file,
    display_mode='ortho',  # we will cut in 3D anyway
    cut_coords=(-40, 0, 0),  # x < 0 for left hemisphere lateral
    title='Left Lateral',
    cmap='gray'
)

# Right lateral
plotting.plot_anat(
    volume_file,
    display_mode='ortho',
    cut_coords=(40, 0, 0),  # x > 0 for right hemisphere lateral
    title='Right Lateral',
    cmap='gray'
)

# Left medial
plotting.plot_anat(
    volume_file,
    display_mode='ortho',
    cut_coords=(20, 0, 0),  # small x > 0 to see medial surface of left
    title='Left Medial',
    cmap='gray'
)

# Right medial
plotting.plot_anat(
    volume_file,
    display_mode='ortho',
    cut_coords=(-20, 0, 0),  # small x < 0 for medial right
    title='Right Medial',
    cmap='gray'
)

# Superior view (top)
plotting.plot_anat(
    volume_file,
    display_mode='z',  # axial slices
    cut_coords=(60,),  # z-coordinate
    title='Superior View',
    cmap='gray'
)

plotting.show()
