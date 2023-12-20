from NNMM.process.value_objects.table_row_index import TableRowIndex


class VideoRowIndex(TableRowIndex):
    pass


if __name__ == "__main__":
    s_row = 1
    video_row_index = VideoRowIndex(s_row)
    print(video_row_index)
