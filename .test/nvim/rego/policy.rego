package kubernetes.admission

default allow := false

allow if {
  input.kind == "Deployment"
}
