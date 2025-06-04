provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}

resource "helm_release" "cluster_autoscaler" {
  name       = "cluster-autoscaler"
  namespace  = "kube-system"
  repository = "https://kubernetes.github.io/autoscaler"
  chart      = "cluster-autoscaler"
  version    = "9.29.0" # adjust as needed

  set {
    name  = "cloudProvider"
    value = "azure"
  }

  set {
    name  = "azureUseManagedIdentity"
    value = "true"
  }

  set {
    name  = "azureClusterName"
    value = "hamzaDevOps"
  }

  set {
    name  = "azureResourceGroup"
    value = "hamza-resources"
  }

  set {
    name  = "rbac.create"
    value = "true"
  }

  set {
    name  = "extraArgs.balance-similar-node-groups"
    value = "true"
  }

  set {
    name  = "extraArgs.expander"
    value = "least-waste"
  }

  set {
    name  = "extraArgs.scan-interval"
    value = "10s"
  }

  set {
    name  = "extraArgs.scale-down-delay-after-add"
    value = "1m"
  }

  set {
    name  = "nodeSelector.kubernetes\\.io/os"
    value = "linux"
  }

  set {
    name  = "tolerations[0].key"
    value = "CriticalAddonsOnly"
  }

  set {
    name  = "tolerations[0].operator"
    value = "Exists"
  }

  set {
    name  = "tolerations[1].key"
    value = "node-role.kubernetes.io/master"
  }

  set {
    name  = "tolerations[1].effect"
    value = "NoSchedule"
  }
}
