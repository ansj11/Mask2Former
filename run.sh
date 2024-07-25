
for filepath in `ls /gemini/data-2/budui/data1205/ | grep "svo" `
do
    echo "processing: ${filepath}"
    python3 -u run_instance_segmentation.py -i "/gemini/data-2/budui/data1205/${filepath}/left/" -o "/gemini/data-2/budui/data1205/${filepath}/mask/" -e png
    echo "finish: ${filepath}"
done


