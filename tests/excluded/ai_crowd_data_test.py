# Simple env test.
import minerl
import os

def main():
    """
    Tests running a simple environment.
    """
    assert "MINERL_DATA_ROOT" in os.environ and os.environ["MINERL_DATA_ROOT"] is not None, "MineRL data required."
 
    os.environ["AICROWD_IS_GRADING"] = "1"
    try:
        d = minerl.data.make('MineRLTreechop-v0', data_dir='/none', num_workers=8)
    except RuntimeError:
        # This will happen if the data is out of date.
        # That is okay.
        pass


    del os.environ["AICROWD_IS_GRADING"]
    try:
        d = minerl.data.make('MineRLTreechop-v0', data_dir='/none', num_workers=8)
        assert False, "The /none directory should not exist."
    except FileNotFoundError:
        pass


    print("Demo complete.")

if __name__ == "__main__":
    main()
