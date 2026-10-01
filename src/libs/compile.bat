python compile.py build_ext --inplace
del "*.c"
move "%cd%\libs\*.pyd" %cd%
ren lz77_cy*.pyd lz77_cy.pyd
ren lz77_huffman_cy*.pyd lz77_huffman_cy.pyd
ren tpl_cy*.pyd tpl_cy.pyd
rmdir /s /q ".\build" ".\libs"