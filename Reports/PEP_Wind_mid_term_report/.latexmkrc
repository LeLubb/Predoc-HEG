# Compiler dans build/ et garder une copie du PDF à côté du fichier .tex.
$pdf_mode = 1;
$out_dir = 'build';
$aux_dir = 'build';
$do_cd = 1;

# Le PDF et SyncTeX restent ensemble dans build/ pour la prévisualisation.
# latexmk protège déjà le chemin substitué à %D par des guillemets.
$success_cmd = 'cp %D .';
