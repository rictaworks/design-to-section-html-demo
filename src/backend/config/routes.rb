Rails.application.routes.draw do
  get "/conversions", to: "conversions#index"
  post "/conversions", to: "conversions#create"
  get "/conversions/:id", to: "conversions#show"
  delete "/conversions/:id", to: "conversions#destroy"
  get "/conversions/:id/source_image", to: "conversions#source_image"

  patch "/conversions/:conversion_id/bands/:band_id", to: "bands#update_kind"
  post "/conversions/:conversion_id/bands/:band_id/merge", to: "bands#merge"
  post "/conversions/:conversion_id/bands/:band_id/split", to: "bands#split"
  post "/conversions/:conversion_id/bands/:band_id/remove", to: "bands#remove"
  post "/conversions/:conversion_id/bands/:band_id/restore", to: "bands#restore"
end
