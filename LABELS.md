# Label Mode

Label mode is a more imperative alternative to autonomous mode, allowing you to specify which specific _per-pod_ whether a pod should be killed, the days/times it can be killed and the probability of it being killed.

Label mode is a good way to have more granular control over which pods are killed at the expense of greater verbosity. This trade-off is especially useful if you have a large number of pods (in the hundreds or even greater magnitudes) but only want to run PowerfulSeal on a few pods, or if your Kubernetes cluster has pods where you want full confidence that PowerfulSeal would not kill.


## Usage

Labels can be manually set using the `kubectl label pods [POD NAME] [LABEL]` command. Once labels are set, label mode can be run by using the `--label` flag. You may also wish to set the `--min-seconds-between-runs` and `--max-seconds-between-runs` flags which default to `0` and `300` respectively.

To reduce the processing time needed to filter a large number of pods, you can instruct PowerfulSeal to only look up pods under a specific namespace by using the `--kubernetes-namespace` argument. This behaves similar to `kubectl`, where not specifying the argument defaults PowerfulSeal to the `default` namespace, whereas specifying an empty value (`--kubernetes-namespace=`) retrieves all pods across all namespaces.

## Example

Suppose we have pods `my-app-1`, `my-app-2`, etc. under the `default` namespace in a system which is designed to handle the failure of one `my-app` pod. In this case, we can make the decision to label the first application pod:

1. To allow PowerfulSeal to act on the pod, run `kubectl label pods my-app-1 seal/enabled=true`
2. To next increase the randomness of when the pod can fail (reflecting the unexpectedness of real world failures), run `kubectl label pods my-app-1 seal/kill-probability=0.5`
3. Finally, to ensure we're present in the office if the resilience of the system fails, we can set labels so that our pod is only killed during working hours with `seal/days="mon,tue,way,thu,fri"`, `seal/start-time=10-00-00` and `seal/end-time=17-30-00`

All of these labels are optional. For additional labels and their defaults, see the reference below.

To finally get PowerfulSeal running, assuming our `kube-config` is at `~/.kube/config` and we'e using the `no-cloud` driver, run: `powerfulseal label --inventory--kubernetes --kube-config ~/.kube/config`.

If we were to change the namespace of the `my-app-*` pods to, for example, `production`, PowerfulSeal can be either run with the `--kubernetes-namespace=production` argument to get all pods with the `production` namespace, or `--kubernetes-namespace=` to get all pods across all namespaces (not recommended due to poor performance when is a large number of pods).

## Reference

| Label                 | Description                                                                                                                             | Default               |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------|-----------------------|
| seal/enabled          | Either "true" or "false"                                                                                                                | "false"               |
| seal/force-kill       | Either "true" or "false"                                                                                                                | "false"               |
| seal/kill-probability | A value between "0" and "1" inclusive describing the probability that a pod should be killed                                            | "1"                   |
| seal/days             | A comma-separated string consisting of "mon", "tue", "wed", "thu", "fri", "sat", "sun", describing the days which the pod can be killed | "mon,tue,wed,thu,fri" |
| seal/start-time       | A value "HH-MM-SS" describing the inclusive start boundary of when a pod can be killed in the local timezone                            | "10-00-00"            |
| seal/end-time         | A value "HH-MM-SS" describing the exclusive end boundary of when a pod can be killed in the local time zone                             | "17-30-00"            |
