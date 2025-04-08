resource "helm_release" "monitoring" {
  name       = "monitoring"
  namespace  = "monitoring"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "45.7.1" # specify chart version if needed
  create_namespace = true

  values = [file("${path.module}/values.yaml")]
}
