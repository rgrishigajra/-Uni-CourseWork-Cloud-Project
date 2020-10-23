import subprocess


def delete_instance(instance_name):
    command = "gcloud compute instances delete %s  --zone us-central1-a --quiet" % (
        instance_name)
    try:
        subprocess.run(command, shell=True, check=True)
    except Exception as e:
        None
    return True


if __name__ == "__main__":
    print("\n\n Running delete sequence:\n")
    delete_instance('master-map-reduce')
    delete_instance('key-value-server4')
