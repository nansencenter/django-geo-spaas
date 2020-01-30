for tag in $*;do
    docker tag "${IMAGE_NAME}" "${IMAGE_NAME}:${tag}"
    docker push "${IMAGE_NAME}:${tag}"
done
